import unittest
from datetime import date
from unittest.mock import Mock, patch

from src.official_chart_engine import (
    build_ecmwf_precipitation_chart_url,
    fetch_ecmwf_precipitation_chart,
)


class TestOfficialChartEngine(unittest.TestCase):
    def test_chart_url_contains_forecast_dimensions(self):
        url = build_ecmwf_precipitation_chart_url(
            base_time=date(2026, 8, 1),
            valid_time=date(2026, 9, 1),
            area="GLOB",
            stats="ensm",
        )
        self.assertIn("seasonal_system5_standard_rain", url)
        self.assertIn("base_time=202608010000", url)
        self.assertIn("valid_time=202609010000", url)
        self.assertIn("stats=ensm", url)

    @patch("src.official_chart_engine.requests.get")
    def test_returns_original_image_url_and_provenance(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "meta": {"license": "CC-BY-4.0", "copyright": "European Centre for Medium-Range Weather Forecasts (ECMWF)"},
            "data": {"data": {"link": {"href": "https://charts.ecmwf.int/content/example.png", "type": "image/png"}}},
        }
        mock_get.return_value = response

        result = fetch_ecmwf_precipitation_chart(forecast_date=date(2026, 8, 27))

        self.assertEqual(result["image_url"], "https://charts.ecmwf.int/content/example.png")
        self.assertEqual(result["license"], "CC-BY-4.0")
        self.assertEqual(result["provider"], "ECMWF")
        self.assertFalse(result["modified"])
        self.assertIn("CC-BY-4.0", result["attribution"])
        self.assertEqual(mock_get.call_count, 1)

    @patch("src.official_chart_engine.requests.get")
    def test_missing_image_is_rejected(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"meta": {"license": "CC-BY-4.0"}, "data": {}}
        mock_get.return_value = response

        with self.assertRaises(ValueError):
            fetch_ecmwf_precipitation_chart(forecast_date=date(2026, 8, 27))


if __name__ == "__main__":
    unittest.main()
