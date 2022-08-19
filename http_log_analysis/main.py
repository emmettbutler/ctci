import argparse
import csv
import logging
import time
from collections import Counter, namedtuple
from typing import Generator

AccessLogEvent = namedtuple(
    "AccessLogEvent",
    ["remotehost", "rfc931", "authuser", "date", "request", "status", "bytes"],
)


def section_from_request(request: str) -> str:
    return f"/{request.split()[1].split('/')[1]}"


class AccessLogAggregate:
    def __init__(
        self,
        bucket_size_seconds: int,
        bucket: int,
        event: AccessLogEvent = None,
    ):
        self.bucket_size_seconds: int = bucket_size_seconds
        self.bucket: int = bucket
        self.latest_time_before_close: int = self.bucket + self.bucket_size_seconds + 30
        self.top_sections: dict = Counter()
        self.total_events: int = 0
        self.is_closed: bool = False

        if event is not None:
            self.total_events = 1
            self.top_sections = Counter([section_from_request(event.request)])

    def __repr__(self):
        return f"<AccessLogAggregate bucket={self.bucket} bucket_size_seconds={self.bucket_size_seconds}>"

    def add(self, unit):
        if self.is_closed:
            logging.warning(f"Received event for already-closed alerting window {self}")
            return

        self.total_events += unit.total_events
        self.top_sections.update(
            {section: count for section, count in unit.top_sections.items()}
        )

    def close(self):
        logging.info(
            f"Bucket={self.bucket}\tBucket size={self.bucket_size_seconds}s\t\tTotal events={self.total_events}\t\t"
            f"Top sections={self.top_sections}"
        )
        self.is_closed = True


class AccessLogMonitor:
    def __init__(self, events, window_size_seconds, threshold):
        self.window_size_seconds = 0
        self.min_window_size_seconds = window_size_seconds
        self.first_event_timestamp = 99999999999
        self.last_event_timestamp = 0
        self.alert_threshold = threshold
        self.events = events
        self.window = []
        self.alert_triggered = False

    def run(self):
        for event in self.events:
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
            if self.window_size_seconds >= self.min_window_size_seconds:
                average_events_per_second = len(self.window) / self.window_size_seconds
                if average_events_per_second > self.alert_threshold:
                    self.log_alert_triggered(average_events_per_second, event.bucket)
                else:
                    self.log_alert_resolved(average_events_per_second, event.bucket)
            yield event

    def log_alert_triggered(self, average_events_per_second, current_time):
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

    def log_alert_resolved(self, average_events_per_second, current_time):
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


def read_access_log(input_file: str, timescale: float) -> Generator:
    """Returns a generator of AccessLogEvent objects"""
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


def snap_to_bucket(timestamp: int, aggregate_seconds: int) -> int:
    """Return the start timestamp of the latest <aggregate_seconds>-second bucket preceding <timestamp>"""
    return timestamp - timestamp % aggregate_seconds


def aggregate_stats(
    units: Generator[AccessLogAggregate, None, None],
    bucket_size_seconds: int,
) -> Generator:
    all_aggregates: dict[int] = {}
    for unit in units:
        # TODO: free closed aggregates after a while
        bucket = snap_to_bucket(unit.bucket, bucket_size_seconds)

        if bucket not in all_aggregates:
            all_aggregates[bucket] = AccessLogAggregate(bucket_size_seconds, bucket)
        all_aggregates[bucket].add(unit)

        for _, aggregate in all_aggregates.items():
            if (
                not aggregate.is_closed
                and unit.bucket > aggregate.latest_time_before_close
                and aggregate.bucket_size_seconds != 0
            ):
                aggregate.close()
        yield unit


def monitor_event_volume(
    events: Generator[AccessLogAggregate, None, None],
    window_size_seconds: int,
    threshold: int,
) -> Generator:
    monitor = AccessLogMonitor(events, window_size_seconds, threshold)
    yield from monitor.run()


def parse_args():
    parser = argparse.ArgumentParser(description="Monitor and analyze HTTP access logs")
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


def main():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    events = read_access_log(args.input_file, args.timescale)
    events = aggregate_stats(events, args.analysis_bucket_size)
    events = monitor_event_volume(events, args.alert_window, args.alert_threshold)
    for event in events:
        pass


if __name__ == "__main__":
    main()
