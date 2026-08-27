import unittest
from unittest.mock import Mock, patch

from src.seasonal_forecast_fetcher import fetch_cfs, fetch_ecmwf, fetch_seasonal_forecasts


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

    @patch("src.seasonal_forecast_fetcher.requests.get")
    def test_ecmwf_never_infers_numeric_values_from_page_text(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = "ECMWF seasonal forecast temperature anomaly: 2.5 C; precipitation: 30 mm"
        mock_get.return_value = response

        result = fetch_ecmwf("2026-08-seasonal-iran")

        self.assertEqual(result["numeric"], {})
        self.assertFalse(result["numeric_source_ready"])
        self.assertIn("2m temperature area averages", result["products"])
        self.assertEqual(mock_get.call_count, 2)

    @patch("src.seasonal_forecast_fetcher.requests.get")
    def test_cfs_source_probe_reports_available_runs_without_fabricating_values(self, mock_get):
        catalog = Mock()
        catalog.raise_for_status.return_value = None
        catalog.text = "CFS catalog"
        root = Mock()
        root.raise_for_status.return_value = None
        root.text = "cfs.20260827/ cfs.20260826/ cfs.20260825/"
        mock_get.side_effect = [catalog, root]

        result = fetch_cfs("2026-08-seasonal-iran")

        self.assertEqual(result["numeric"], {})
        self.assertTrue(result["numeric_source_ready"])
        self.assertEqual(result["latest_runs"], ["20260827", "20260826", "20260825"])
        self.assertEqual(result["format"], "GRIB2")


if __name__ == "__main__":
    unittest.main()
