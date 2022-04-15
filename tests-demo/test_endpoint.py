import requests
import unittest


AUTH_TOKEN = "WyIyMDA3IiwiJDUkcm91bmRzPTUzNTAwMCQ4czdkZ0lyZkxRalN1TXlkJHZJbXJPMzFVdERYZDFlTDRZTmdDaHJwUjBhRmIydW0vampvQWYzTE1iUzYiXQ.Yk-w_w.dGRb3xdsG6TgzOTHYdhh0eSmHWk"


def do_request(params, auth_token=AUTH_TOKEN, include_headers=True):
    BASE_URL = "https://app.raptormaps.com"
    endpoint = "%s/api/v2/solar_farms" % (BASE_URL)
    headers = {"content-type": "application/json", "Authentication-Token": auth_token}

    return requests.get(
        endpoint, headers=headers if include_headers else None, params=params
    )


class TestEndpoint(unittest.TestCase):
    def test_correct_input(self):
        response = do_request({"org_id": 228})
        self.assertEqual(
            response.status_code,
            200,
            "A well-formed request returns a well-formed response",
        )
        solar_farms = response.json().get("solar_farms")
        for farm in solar_farms:
            self.assertTrue(
                farm.get("uuid"), "A well-formed request returns a well-formed response"
            )

    def test_wrong_parameter(self):
        response = do_request({"org_ids": 228})
        self.assertEqual(
            response.status_code,
            400,
            "sending an unrecognized parameter results in a 400 error",
        )

    def test_no_auth(self):
        response = do_request({"org_id": 228}, include_headers=False)
        self.assertEqual(
            response.status_code,
            401,
            "sending no auth header results in a 401 error",
        )

    def test_wrong_auth(self):
        response = do_request({"org_id": 227})
        self.assertEqual(
            response.status_code,
            403,
            "requesting an unauthorized org results in a 403 error",
        )


if __name__ == "__main__":
    unittest.main()
