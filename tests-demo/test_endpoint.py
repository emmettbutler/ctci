import requests
import unittest


def do_request():
    BASE_URL = "https://app.raptormaps.com"
    auth_token = "WyIyMDA3IiwiJDUkcm91bmRzPTUzNTAwMCQ4czdkZ0lyZkxRalN1TXlkJHZJbXJPMzFVdERYZDFlTDRZTmdDaHJwUjBhRmIydW0vampvQWYzTE1iUzYiXQ.Yk-w_w.dGRb3xdsG6TgzOTHYdhh0eSmHWk"
    endpoint = "%s/api/v2/solar_farms" % (BASE_URL)
    headers = {"content-type": "application/json", "Authentication-Token": auth_token}

    return requests.get(endpoint, headers=headers, params={"org_id": 228})


class TestEndpoint(unittest.TestCase):
    def test_correct_input(self):
        data = do_request().json()
        solar_farms = data.get("solar_farms")
        for farm in solar_farms:
            self.assertTrue(farm.get("uuid"))


if __name__ == "__main__":
    unittest.main()
