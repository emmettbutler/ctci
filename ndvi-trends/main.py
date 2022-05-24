import io
import requests

from PIL import Image

oauth_response = requests.post(
    "https://services.sentinel-hub.com/oauth/token",
    headers={"content-type": "application/x-www-form-urlencoded"},
    data={
        "grant_type": "client_credentials",
        "client_id": "24acc842-553a-47b5-a091-d4e6e2612392",
        "client_secret": "gi:E]inm71Kjr~~2-(:]nh,CsFdLx03g&9Rr#p1O",
    },
)

token = oauth_response.json()["access_token"]

response = requests.post(
    "https://services.sentinel-hub.com/api/v1/process",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    },
    json={
        "input": {
            "bounds": {
                "bbox": [
                    13.822174072265625,
                    45.85080395917834,
                    14.55963134765625,
                    46.29191774991382,
                ]
            },
            "data": [{"type": "sentinel-2-l2a"}],
        },
        "evalscript": """
        //VERSION=3

    function setup() {
      return {
        input: ["B08", "B04"],
        output: {
          bands: 1
        }
      };
    }

    function evaluatePixel(
      sample,
      scenes,
      inputMetadata,
      customData,
      outputMetadata
    ) {
      return [(sample.B08 - sample.B04) / (sample.B08 + sample.B04)];
    }
    """,
    },
)

image = Image.open(io.BytesIO(response.content))
image.show()
histogram = image.histogram()
avg = 0
for count, value in enumerate(histogram):
    avg += count * value
avg /= sum(histogram)
print(f"avg NDVI: {avg}")
