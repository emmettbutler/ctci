import argparse
import csv
import logging
import time
from collections import Counter, deque, namedtuple
from typing import Generator

# generating this namedtuple from the file's header would make it handle log schema changes
AccessLogEvent = namedtuple(
    "AccessLogEvent",
    ["remotehost", "rfc931", "authuser", "date", "request", "status", "bytes"],
)


class AccessLogAggregate:
    def __init__(
        self,
        bucket_size_seconds: int,
        bucket: int,
        event: AccessLogEvent = None,
    ):
        """Create an aggregate over a time-grouping of other AccessLogAggregates

        :param bucket_size_seconds: The size of the time bucket represented by this aggregate
        :param bucket: The epoch timestamp of the beginning of the time bucket represented by this aggregate
        :param event: An event that, if given, initializes analysis counters for the aggregate
        """
        self.bucket_size_seconds: int = bucket_size_seconds
        self.bucket: int = bucket
        # allow events to join this aggregate up to 30 seconds after its bucket has ended
        # accounts for out-of-order event arrival
        self.latest_time_before_close: int = self.bucket + self.bucket_size_seconds + 30
        self.top_sections: dict = Counter()
        self.total_events: int = 0
        self.is_closed: bool = False

        if event is not None:
            self.total_events = 1
            self.top_sections = Counter([section_from_request(event.request)])

    def __repr__(self):
        return f"<AccessLogAggregate bucket={self.bucket} bucket_size_seconds={self.bucket_size_seconds}>"

    def add(self, aggregate):
        """Update analysis counters with information from the given aggregate"""
        if self.is_closed:
            logging.warning(f"Received event for already-closed alerting window {self}")
            return

        self.total_events += aggregate.total_events
        self.top_sections.update(
            {section: count for section, count in aggregate.top_sections.items()}
        )

    def close(self):
        """Mark this aggregate as closed and log its collected stats"""
        logging.info(
            f"Bucket={self.bucket}\tBucket size={self.bucket_size_seconds}s\t\tTotal events={self.total_events}\t\t"
            f"Top sections={self.top_sections}"
        )
        self.is_closed = True


class AccessLogMonitor:
    def __init__(
        self,
        events: Generator[AccessLogAggregate, None, None],
        window_size_seconds: int,
        threshold: int,
    ):
        """Create a monitor over AccessLogAggregates based on a sliding window

        :param events: The sequence of aggregates over which to perform monitoring
        :param window_size_seconds: The size of the sliding window used for analysis, in seconds
        :param threshold: The number of events per second on average over the monitoring window that will cause an alert
            to trigger
        """
        self.window_size_seconds = 0
        self.min_window_size_seconds = window_size_seconds
        self.first_event_timestamp = 99999999999
        self.last_event_timestamp = 0
        self.alert_threshold = threshold
        self.events = events
        self.window = []
        self.alert_triggered = False

    def run(self):
        """Monitor the sequence of aggregates"""
        for event in self.events:
            self.update_window(event)
            if self.window_size_seconds >= self.min_window_size_seconds:
                self.evaluate_alert_conditions(event.bucket)
            yield event

    def update_window(self, event: AccessLogAggregate):
        """Add the given event to the analysis window

        Maintains a sliding window by expelling old events as new ones are added
        Tracks the size of the window in seconds
        """
        self.window = [
            e
            for e in self.window
            if e.bucket >= event.bucket - self.min_window_size_seconds
        ]
        self.window.append(event)
        self.first_event_timestamp = min(self.window[0].bucket, event.bucket)
        self.last_event_timestamp = max(self.window[-1].bucket, event.bucket)
        self.window_size_seconds = (
            self.last_event_timestamp - self.first_event_timestamp
        )

    # this only has one alert condition, but it would be straightforward to make it loop over multiple alert conditions
    def evaluate_alert_conditions(self, timestamp: int):
        """Check the alert conditions and trigger alerts if applicable

        :param timestamp: The current time
        """
        average_events_per_second = len(self.window) / (self.window_size_seconds or 1)
        if average_events_per_second > self.alert_threshold:
            self.trigger_alert(average_events_per_second, timestamp)
            return True
        else:
            self.resolve_alert(average_events_per_second, timestamp)
            return False

    def trigger_alert(self, average_events_per_second, current_time):
        if not self.alert_triggered:
            self.alert_triggered = True
            logging.warning(
                f"High traffic generated an alert - hits = {average_events_per_second:.2f}/s, "
                f"triggered at {current_time}"
            )
            logging.debug(
                f"window_size={self.window_size_seconds}s\t\tTotal events={len(self.window)}\t\t"
                f"avg_events_per_second={average_events_per_second:.2f}\t"
                f"More than {self.alert_threshold} events per second"
            )

    def resolve_alert(self, average_events_per_second, current_time):
        if self.alert_triggered:
            self.alert_triggered = False
            logging.warning(
                f"Reduced traffic resolved an alert - hits = {average_events_per_second:.2f}/s, "
                f"resolved at {current_time}"
            )
            logging.debug(
                f"window_size={self.window_size_seconds}s\t\tTotal events={len(self.window)}\t\t"
                f"avg_events_per_second={average_events_per_second}\t"
                f"Fewer than {self.alert_threshold} events per second"
            )


def read_access_log(
    input_file: str, timescale: float
) -> Generator[AccessLogAggregate, None, None]:
    """Generates AccessLogAggregates from a CSV HTTP access logfile with a schema conforming to AccessLogEvent

    Simulates delayed event arrival with time.sleep.
    Minimizes memory usage by lazily reading from disk.

    :param input_file: The relative path of the file from which to read access logs
    :param timescale: A multiplier applied to the sleep time between events. The sleep time defaults to the difference
        between the each pair of event timestamps in the log.
    """
    current_timestamp = 0
    with open(input_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        for row in reader:
            event = AccessLogEvent(**row)
            time.sleep(
                (
                    max(int(event.date) - current_timestamp, 0)
                    if current_timestamp
                    else 0
                )
                * timescale
            )
            current_timestamp = int(event.date)
            logging.debug(event)
            aggregate = AccessLogAggregate(0, current_timestamp, event)
            logging.debug(aggregate)
            yield aggregate


def aggregate_stats(
    aggregates: Generator[AccessLogAggregate, None, None],
    bucket_size_seconds: int,
) -> Generator:
    """Collect and report statistics on time-bucketed aggregates over the <aggregates> generator

    :param aggregates: The sequence over which to aggregate
    :param bucket_size_seconds: The size in seconds of the aggregation buckets to analyze
    """
    all_aggregates: dict[int] = {}
    for agg in aggregates:
        bucket = agg.bucket - agg.bucket % bucket_size_seconds

        if bucket not in all_aggregates:
            all_aggregates[bucket] = AccessLogAggregate(bucket_size_seconds, bucket)
        all_aggregates[bucket].add(agg)

        # handle out-of-order arrival by closing aggregates that haven't gotten new data in a while
        for _, aggregate in all_aggregates.items():
            if (
                not aggregate.is_closed
                and agg.bucket > aggregate.latest_time_before_close
                and aggregate.bucket_size_seconds != 0
            ):
                aggregate.close()

        # free the memory occupied by closed aggregates
        all_aggregates = {k: v for k, v in all_aggregates.items() if not v.is_closed}

        yield agg


def parse_args():
    parser = argparse.ArgumentParser(
        description="Monitor and analyze a CSV HTTP access log with a schema conforming to AccessLogEvent. "
        "Simulates delayed event arrival with time.sleep."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="CSV file from which to read log",
    )
    parser.add_argument(
        "--alert-threshold",
        "-a",
        type=int,
        default=10,
        help="Average requests per second during the monitoring window above which to alert. Defaults to 10.",
    )
    parser.add_argument(
        "--alert-window",
        "-w",
        type=int,
        default=120,
        help="The size in seconds of the rolling window over which alerts are evaluated. Defaults to 120.",
    )
    parser.add_argument(
        "--analysis-bucket-size",
        "-b",
        type=int,
        default=10,
        help="The size in seconds of the aggregation buckets in which alerts are analyzed. Defaults to 10.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--timescale",
        "-t",
        type=float,
        default=0,
        help="How fast events should play back. Set between 0 and 1 for faster playback, above 1 for slower. "
        "Defaults to 0 (no playback delay)",
    )
    return parser.parse_args()


def section_from_request(request: str) -> str:
    """Given a request string from an access log, return the section name"""
    return f"/{request.split()[1].split('/')[1]}"


def exhaust(generator: Generator):
    """Consume the given generator using a minimum of resources"""
    deque(generator, maxlen=0)


def main():
    """Analyze and monitor an HTTP access log. See --help for more details."""
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    events = read_access_log(args.input_file, args.timescale)
    events = aggregate_stats(events, args.analysis_bucket_size)
    events = AccessLogMonitor(events, args.alert_window, args.alert_threshold).run()
    exhaust(events)


if __name__ == "__main__":
    main()
