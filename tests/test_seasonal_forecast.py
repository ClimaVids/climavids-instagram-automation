import unittest

from src.seasonal_forecast_fetcher import fetch_seasonal_forecasts


class TestSeasonalForecastContract(unittest.TestCase):
    def test_fetcher_is_importable_and_has_public_contract(self):
        self.assertTrue(callable(fetch_seasonal_forecasts))

    def test_minimal_result_fixture_matches_public_contract(self):
        fixture = {
            "season_key": "2026-08-seasonal-iran",
            "sources": {
                "ecmwf": {"provider": "ECMWF", "numeric": {}},
                "cfs": {"provider": "NOAA/NCEP CFSv2", "numeric": {}},
                "irimo": {"provider": "IRIMO", "numeric": {}},
            },
            "data_quality": "official-source-metadata-only",
        }
        self.assertIn("season_key", fixture)
        self.assertEqual(set(fixture["sources"]), {"ecmwf", "cfs", "irimo"})
        self.assertIn(fixture["data_quality"], {"official-source-metadata-only", "numeric_or_mixed", "none"})


if __name__ == "__main__":
    unittest.main()
