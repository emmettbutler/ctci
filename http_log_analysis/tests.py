import unittest
from unittest.mock import Mock

from main import AccessLogAggregate, aggregate_stats, section_from_request


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


if __name__ == "__main__":
    unittest.main()
