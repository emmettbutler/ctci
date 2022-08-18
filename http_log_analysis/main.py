import datetime as dt
import logging
from collections import defaultdict, namedtuple
from typing import Generator, Tuple

AccessLogEvent = namedtuple(
    "AccessLogEvent",
    ["remotehost", "rfc931", "authuser", "date", "request", "status", "bytes"],
)


class AccessLogAggregate:
    def __init__(
        self,
        bucket_size_seconds: int,
        bucket: dt.datetime,
    ):
        self.bucket_size_seconds: int = bucket_size_seconds
        self.bucket: dt.datetime = bucket
        self.latest_time_before_close: dt.datetime = self.bucket + dt.timedelta(
            seconds=self.bucket_size_seconds + 30
        )
        self.first_event_timestamp: dt.datetime = dt.datetime.max
        self.last_event_timestamp: dt.datetime = dt.datetime.min
        self.top_sections: dict = defaultdict(int)
        self.total_events: int = 0
        self.is_closed: bool = False

    def __repr__(self):
        return f"<AccessLogAggregate bucket={self.bucket.timestamp()} bucket_size_seconds={self.bucket_size_seconds}>"

    def add(self, unit):
        if self.is_closed:
            logging.warning(f"Received event for already-closed alerting window {self}")
            return

        self.total_events += unit.total_events
        self.first_event_timestamp = min(
            self.first_event_timestamp, unit.first_event_timestamp
        )
        self.last_event_timestamp = max(
            self.last_event_timestamp, unit.last_event_timestamp
        )
        # TODO add top sections from unit

    def log_stats(self):
        logging.info("----------------")
        logging.info(f"Bucket: {self.bucket.timestamp()}")
        logging.info(f"Total events: {self.total_events}")
        logging.info("----------------")

    def evaluate_alerts(self):
        logging.info("Here are some alerts")

    def close(self):
        self.is_closed = True


def read_access_log() -> Generator:
    return ()


def snap_to_bucket(timestamp: int, aggregate_seconds: int) -> int:
    """Round the given timestamp to the boundary of the latest preceding <aggregate_seconds>-second bucket"""
    return 0


def make_aggregates(
    units: Generator[AccessLogAggregate | AccessLogEvent],
    bucket_sizes_seconds: Tuple[int],
    size_index: int = 0,
) -> Generator:
    bucket_sizes_seconds = sorted(set(bucket_sizes_seconds))
    open_aggregates: dict[int, dict[int]] = {
        bucket_size: {} for bucket_size in bucket_sizes_seconds
    }
    for unit in units:
        aggregate_seconds = bucket_sizes_seconds[size_index]
        # TODO: free closed aggregates after a while
        aggregates_for_size = open_aggregates[aggregate_seconds]
        bucket = snap_to_bucket(unit.bucket, aggregate_seconds)

        if bucket not in open_aggregates:
            aggregates_for_size[bucket] = AccessLogAggregate(aggregate_seconds, bucket)
        aggregates_for_size[bucket].add(unit)

        if False and size_index < len(bucket_sizes_seconds) - 1:  # when to recurse?
            yield from make_aggregates(
                aggregates_for_size.values(), bucket_sizes_seconds[size_index + 1]
            )

        for _, open_aggregate in aggregates_for_size.items():
            if unit.bucket > open_aggregate.latest_time_before_close:
                yield open_aggregate
                open_aggregate.close()


def main():
    aggregates = make_aggregates(read_access_log(), (10, 60 * 2))
    for aggregate in aggregates:
        aggregate.log_stats()
        aggregate.evaluate_alerts()


if __name__ == "__main__":
    main()
