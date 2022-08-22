import logging
import os
import unittest
from copy import deepcopy
from unittest.mock import Mock

from main import (
    AccessLogAggregate,
    AccessLogMonitor,
    aggregate_stats,
    read_access_log,
    section_from_request,
)

logging.basicConfig(level=logging.ERROR)


class HTTPLogAnalyzerUnitTests(unittest.TestCase):
    def setUp(self):
        agg1 = Mock(spec=AccessLogAggregate)
        agg1.bucket = 123456789
        agg1.total_events = 1
        agg1.top_sections = {}
        agg1.top_hosts = {}
        agg1.top_status_codes = {}
        agg1.availability = {}
        agg1.bytes = 0
        agg2 = deepcopy(agg1)
        agg2.bucket = 123456589
        self.events = [agg1, agg2]

    def test_section_from_request(self):
        result = section_from_request("GET /api/user HTTP/1.0")
        assert (
            result == "/api"
        ), "section_from_request() should extract the correct section"

    def test_read_access_log_and_parse_event(self):
        here = os.path.dirname(os.path.abspath(__file__))
        result = list(read_access_log(os.path.join(here, "readme_sample_csv.txt"), 0))
        assert len(result) == 4830, "read_access_log should consume the entire log file"
        assert isinstance(
            result[0], AccessLogAggregate
        ), "read_access_log should return a sequence of AccessLogAggregates"
        assert result[0].bucket == 1549573860
        assert (
            result[0].bucket_size_seconds == 0
        ), "Parsing step should return aggregates representing individual events"
        assert result[0].top_sections == {"/api": 1}
        assert result[0].top_hosts == {"10.0.0.2": 1}
        assert result[0].top_status_codes == {"200": 1}
        assert result[0].availability["total"] == 1
        assert result[0].availability["successes"] == 1
        assert result[0].availability["failures"] == 0
        assert result[0].bytes == 1234
        assert result[0].is_closed is False
        assert result[0].latest_time_before_close > 0

    def test_read_access_log_containing_malformed_lines_and_parse_event(self):
        here = os.path.dirname(os.path.abspath(__file__))
        result = list(
            read_access_log(
                os.path.join(here, "sample_csv_with_malformed_lines.txt"), 0
            )
        )
        assert (
            len(result) == 4830
        ), "read_access_log should consume the entire log file, ignoring malformed lines"
        assert isinstance(
            result[0], AccessLogAggregate
        ), "read_access_log should return a sequence of AccessLogAggregates"
        assert result[0].bucket == 1549573860
        assert (
            result[0].bucket_size_seconds == 0
        ), "Parsing step should return aggregates representing individual events"
        assert result[0].top_sections == {"/api": 1}
        assert result[0].top_hosts == {"10.0.0.2": 1}
        assert result[0].top_status_codes == {"200": 1}
        assert result[0].availability["total"] == 1
        assert result[0].availability["successes"] == 1
        assert result[0].availability["failures"] == 0
        assert result[0].bytes == 1234
        assert result[0].is_closed is False
        assert result[0].latest_time_before_close > 0

    def test_aggregate_stats(self):
        result = list(aggregate_stats(self.events, 10))
        assert result == self.events

    def test_monitor_alerts(self):
        monitor = AccessLogMonitor(self.events, 1, 0)
        monitor.update_window(self.events[1])
        assert monitor.evaluate_alert_conditions(
            12345
        ), "Monitor evaluation exceeding threshold should trigger alert"

    def test_monitor_resolves(self):
        monitor = AccessLogMonitor(self.events, 1, 2)
        monitor.update_window(self.events[1])
        monitor.alert_triggered = True
        assert (
            monitor.evaluate_alert_conditions(self.events[1].bucket + 10) is False
        ), "Monitor evaluation on triggered monitor not exceeding threshold should resolve alert"

    def test_monitor_does_not_alert(self):
        monitor = AccessLogMonitor(self.events, 1, 2)
        monitor.update_window(self.events[1])
        monitor.evaluate_alert_conditions(self.events[1].bucket + 10)
        assert (
            monitor.alert_triggered is False
        ), "Monitor evaluation on untriggered monitor not exceeding threshold should not trigger an alert"

    def test_monitor_does_not_flap(self):
        here = os.path.dirname(os.path.abspath(__file__))
        events = read_access_log(os.path.join(here, "readme_sample_csv.txt"), 0)
        events_between_flappy_timestamps = 0

        def debugcounter(_events):
            nonlocal events_between_flappy_timestamps
            for event in _events:
                # these are the earliest and latest timestamps of a range of the sample logfile in which the monitor
                # alerts erroneously. This test confirms that the logfile contains an average of 10.008333 events that
                # occur per second between these two particular timestamps.
                # we want to make sure that the monitor only triggers twice for this entire file.
                if event.bucket <= 1549574044 and event.bucket >= 1549573924:
                    events_between_flappy_timestamps += 1
                yield event

        monitor = AccessLogMonitor(debugcounter(events), 120, 10.0)
        for _ in monitor.run():
            pass
        assert (
            events_between_flappy_timestamps == 1201
        ), "Exactly 1201 events should have been counted in the given time range"
        assert (
            monitor.times_alert_triggered == 2
        ), "Given this specific input file, the alert should trigger exactly twice."

    def test_aggregate_add(self):
        event = {
            "remotehost": "10.0.0.1",
            "rfc931": "-",
            "authuser": "apache",
            "date": "1549574332",
            "request": "GET /api/user HTTP/1.0",
            "status": "200",
            "bytes": "1234",
        }
        agg = AccessLogAggregate(0, 12345, event)
        agg.add(AccessLogAggregate(0, 12346, event))
        assert (
            agg.availability["total"] == 2
        ), "total events counting from AccessLogAggregate.add should be accurate"
        assert (
            agg.top_sections["/api"] == 2
        ), "top section counting from AccessLogAggregate.add should be accurate"
        assert agg.top_hosts == {"10.0.0.1": 2}
        assert agg.top_status_codes == {"200": 2}
        assert agg.availability["successes"] == 2
        assert agg.availability["failures"] == 0
        assert agg.bytes == 2468


if __name__ == "__main__":
    unittest.main()
