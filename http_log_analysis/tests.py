import unittest
from unittest.mock import Mock

from main import (AccessLogAggregate, AccessLogEvent, AccessLogMonitor,
                  aggregate_stats, read_access_log, section_from_request)


class HTTPLogAnalyzerUnitTests(unittest.TestCase):
    def test_section_from_request(self):
        result = section_from_request("GET /api/user HTTP/1.0")
        assert (
            result == "/api"
        ), "section_from_request() should extract the correct section"

    def test_aggregate_stats(self):
        agg1 = Mock(spec=AccessLogAggregate)
        agg1.bucket = 123456789
        agg1.total_events = 1
        agg1.top_sections = {}
        agg2 = Mock(spec=AccessLogAggregate)
        agg2.bucket = 123456589
        agg2.total_events = 1
        agg2.top_sections = {}
        aggregates = (a for a in [agg1, agg2])
        result = list(aggregate_stats(aggregates, 10))
        assert (
            len(result) == 2
        ), "aggregate_stats should return the same generator it consumed"
        assert result[0] == agg1
        assert result[1] == agg2

    def test_read_access_log(self):
        result = list(read_access_log("readme_sample_csv.txt", 0))
        assert len(result) == 4830, "read_access_log should consume the entire log file"
        assert isinstance(
            result[0], AccessLogAggregate
        ), "read_access_log should return a sequence of AccessLogAggregates"


class AccessLogMonitorUnitTests(unittest.TestCase):
    def setUp(self):
        agg1 = Mock(spec=AccessLogAggregate)
        agg1.bucket = 123456789
        agg1.total_events = 1
        agg1.top_sections = {}
        agg2 = Mock(spec=AccessLogAggregate)
        agg2.bucket = 123456589
        agg2.total_events = 1
        agg2.top_sections = {}
        self.events = [agg1, agg2]

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


class AccessLogAggregateUnitTests(unittest.TestCase):
    def test_aggregate_add(self):
        event = AccessLogEvent(
            "10.0.0.1", "-", "apache", 1549574332, "GET /api/user HTTP/1.0", 200, 1234
        )
        agg = AccessLogAggregate(0, 12345, event)
        agg.add(AccessLogAggregate(0, 12346, event))
        assert agg.total_events == 2, "total events counting from AccessLogAggregate.add should be accurate"
        assert agg.top_sections["/api"] == 2, "top section counting from AccessLogAggregate.add should be accurate"


if __name__ == "__main__":
    unittest.main()
