from main import load_forecast, make_forecast_dataframe, enrich_forecast


weather_data = load_forecast(data_path="fixture.json")
dataframe = None


def test_load_forecast():
    assert len(weather_data.keys()) == 5, "loaded data has expected format"
    assert weather_data["cnt"] == 40, "loaded data has expected count"
    assert (
        len(weather_data["list"]) == 40
    ), "loaded data has expected number of forecast elements"


def test_make_forecast_dataframe():
    global dataframe
    dataframe = make_forecast_dataframe(weather_data)
    assert len(dataframe.columns) == 5, "generated dataframe has expected column count"
    assert "temp_C" in dataframe.columns, "an expected column is present"
    assert isinstance(
        dataframe.iloc[0].wind_speed, float
    ), "a wind_speed entry has the correct type"
    assert "temp_F" not in dataframe.columns, "an unexpected column is not present"


def test_enrich_forecast():
    enriched = enrich_forecast(dataframe)
    assert (
        "temp_F" in enriched.columns
    ), "an enrichment column is present after enrichments"
    assert (
        enriched.iloc[0].temp_F != enriched.iloc[0].temp_C
    ), "C and F temp are different"
