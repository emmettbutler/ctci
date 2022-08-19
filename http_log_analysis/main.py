import csv
import logging
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

    def log_stats(self):
        logging.info("----------------")
        logging.info(f"Bucket: {self.bucket}")
        logging.info(f"Bucket size: {self.bucket_size_seconds}s")
        logging.info(f"Total events: {self.total_events}")
        logging.info(f"Top sections: {self.top_sections}")
        logging.info("----------------")

    def evaluate_alert(self):
        return self.total_events > self.bucket_size_seconds * 10

    def log_alert_triggered(self):
        logging.warning(
            "More than 10 events per second over the current two-minute period"
        )

    def log_alert_resolved(self):
        logging.warning("Event volume fell below 10 events per second")

    def close(self):
        self.is_closed = True


def read_access_log() -> Generator:
    """Returns a generator of AccessLogEvent objects"""
    with open("readme_sample_csv.txt", newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        for row in reader:
            event = AccessLogEvent(**row)
            logging.debug(event)
            aggregate = AccessLogAggregate(0, int(event.date), event)
            logging.debug(aggregate)
            yield aggregate


def snap_to_bucket(timestamp: int, aggregate_seconds: int) -> int:
    """Return the start timestamp of the latest <aggregate_seconds>-second bucket preceding <timestamp>"""
    return timestamp - timestamp % aggregate_seconds


def make_aggregates(
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
            ):
                yield aggregate
                aggregate.close()


def log_stats(
    aggregates: Generator[AccessLogAggregate, None, None],
) -> Generator[AccessLogAggregate, None, None]:
    for aggregate in aggregates:
        aggregate.log_stats()
        yield aggregate


def evaluate_alerts(
    aggregates: Generator[AccessLogAggregate, None, None],
) -> Generator[AccessLogAggregate, None, None]:
    is_alerting = False
    for aggregate in aggregates:
        alert_triggered = aggregate.evaluate_alert()
        if not is_alerting and alert_triggered:
            is_alerting = True
            aggregate.log_alert_triggered()
        if is_alerting and not alert_triggered:
            is_alerting = False
            aggregate.log_alert_resolved()
        yield aggregate


def main():
    logging.basicConfig(level=logging.INFO)

    log_entries = read_access_log()
    aggs = make_aggregates(log_entries, 10)
    aggs = log_stats(aggs)
    aggs = make_aggregates(aggs, 60 * 2)
    aggs = evaluate_alerts(aggs)
    for agg in aggs:
        pass


if __name__ == "__main__":
    main()
