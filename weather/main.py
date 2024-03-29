import datetime as dt
import simplejson as json
import logging as log
import os
import requests

import pandas as pd


OPENWEATHER_APIKEY = "c46c557e9993060ab2083ab71d14c510"
OPENWEATHER_CITY_ID = "2643743"
FORECAST_PATH = "weatherdata.json"
EXPECTED_ROW_COUNT = 40  # five days of eight forecasts per day
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def load_forecast(data_path=FORECAST_PATH):
    """Load OpenWeather API response data from a local file or the internet"""
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            forecast = json.loads(f.read())
    else:
        payload = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast?id={OPENWEATHER_CITY_ID}&units=metric&appid={OPENWEATHER_APIKEY}"
        )
        with open(FORECAST_PATH, "w") as f:
            f.write(payload.text)
        forecast = payload.json()
    forecast_count = forecast.get("cnt")
    if forecast_count > 0:
        if forecast_count < EXPECTED_ROW_COUNT:
            log.warning(
                "Fewer than 40 rows returned from OpenWeather - some 3-hourly forecast data may be unavailable"
            )
        return forecast
    else:
        log.warning("Zero forecast rows returned from OpenWeather")


def make_forecast_dataframe(weather_data):
    """Turn weather data from OpenWeather API into a specially-formatted forecast dataframe"""
    forecast = []
    for day_data in weather_data.get("list", []):
        date = dt.datetime.utcfromtimestamp(day_data.get("dt", 0))
        day_main = day_data.get("main", {})
        temp = day_main.get("temp")
        temp_min = day_main.get("temp_min")
        temp_max = day_main.get("temp_max")
        wind_speed = day_data.get("wind", {}).get("speed", 0)
        forecast.append(
            {
                "dt": date.strftime(DATE_FORMAT),
                "temp_C": temp,
                "temp_min_C": temp_min,
                "temp_max_C": temp_max,
                "wind_speed": wind_speed,
            }
        )
    return pd.DataFrame.from_records(forecast)


def enrich_forecast(forecast):
    """Add synthetic columns to dataframe"""
    forecast["dt_minus_1h"] = pd.to_datetime(forecast["dt"]) - pd.to_timedelta(
        1, unit="H"
    )
    forecast["temp_F"] = 32 + forecast["temp_C"] * (9 / 5)
    return forecast


def main():
    weather_data = load_forecast()
    if weather_data is None:
        log.error("No well-formed weather information could be found")
    forecast_dataframe = make_forecast_dataframe(weather_data)
    enriched_dataframe = enrich_forecast(forecast_dataframe)
    enriched_dataframe.to_csv("forecast.csv")

    # keep this script, and thus the container, running to enable inspection
    input()


if __name__ == "__main__":
    main()
