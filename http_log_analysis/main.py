import datetime as dt
from collections import defaultdict, namedtuple
from typing import Generator, Tuple

AccessLogEvent = namedtuple(
    "AccessLogEvent",
    ["remotehost", "rfc931", "authuser", "date", "request", "status", "bytes"],
)


class AccessLogEvent:
    @property
    def bucket() -> dt.datetime:
        return


class AccessLogAggregate:
    def __init__(
        self,
        max_bucket_size_seconds: int,
        bucket: dt.datetime,
    ):
        self.max_bucket_size_seconds: int = max_bucket_size_seconds
        self.bucket: dt.datetime = bucket
        self.first_event_timestamp: dt.datetime = dt.datetime.max
        self.last_event_timestamp: dt.datetime = dt.datetime.min
        self.top_sections: dict = defaultdict(int)
        self.total_events: int = 0

    def add(self, unit):
        if self.is_closed:
            pass  # log warning
        pass

    def log_stats(self):
        pass

    def evaluate_alerts(self):
        pass

    @property
    def bucket_timestamp(self) -> int:
        return 0

    def close(self):
        pass

    @property
    def is_closed(self):
        pass


def read_access_log() -> Generator:
    return ()


def snap_to_bucket(timestamp: int, aggregate_seconds: int) -> int:
    """Round the given timestamp to the boundary of the latest preceding <aggregate_seconds>-second bucket"""
    return 0


def make_aggregates(
    units: Generator[AccessLogAggregate | AccessLogEvent],
    bucket_sizes_seconds: Tuple[int],
) -> Generator:
    open_aggregates: dict[int, dict[int]] = {
        bucket_size: {} for bucket_size in bucket_sizes_seconds
    }
    for unit in units:
        for aggregate_seconds in bucket_sizes_seconds:
            # TODO: free closed aggregates after a while
            aggregates_for_size = open_aggregates[aggregate_seconds]
            bucket = snap_to_bucket(unit.date, aggregate_seconds)
            if bucket not in open_aggregates:
                aggregates_for_size[bucket] = AccessLogAggregate(
                    aggregate_seconds, bucket
                )

            aggregates_for_size[bucket].add(unit)

            for _, open_aggregate in aggregates_for_size.items():
                if unit.date > open_aggregate.latest_time_before_close:
                    yield open_aggregate
                    open_aggregate.close()


def main():
    aggregates = make_aggregates(read_access_log(), (10, 60 * 2))
    for aggregate in aggregates:
        aggregate.log_stats()
        aggregate.evaluate_alerts()


if __name__ == "__main__":
    main()
