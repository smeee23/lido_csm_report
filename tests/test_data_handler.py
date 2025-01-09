import unittest
from unittest.mock import Mock, patch
import json
from DataHandler import DataHandler

class TestDataHandler(unittest.TestCase):
    def setUp(self):
        self.handler = DataHandler()
        self.mock_s3 = Mock()
        
        # Sample test data matching the provided format
        self.test_data = {
            "2024-12-24": {
                "validatorCount": 6,
                "sumMissedAttestations": 0,
                "sumInclusionDelay": 1421,
                "avgInclusionDelay": 1.0525925925925925
            }
        }

    def test_normalize_data(self):
        input_data = {
            "2024-12-24": {
                "validatorCount": 10,
                "sumMissedAttestations": 50,
                "sumInclusionDelay": 1000,
                "totalUniqueAttestations": 1000
            }
        }
        
        normalized = self.handler.normalize_data(input_data)
        self.assertEqual(normalized["2024-12-24"]["validatorCount"], {"metric": 10})
        self.assertEqual(normalized["2024-12-24"]["sumMissedAttestations"], {'metric': 50, 'per_val': 5.0, 'attest_pct': 5.0})
        self.assertEqual(normalized["2024-12-24"]["sumInclusionDelay"], {"metric": 1000})
        self.assertEqual(normalized["2024-12-24"]["totalUniqueAttestations"], {"metric": 1000})
        
    def test_normalize_data_handles_none(self):
        input_data = {
            "2024-12-24": {
                "validatorCount": 10,
                "sumMissedAttestations": None,
            }
        }
        
        normalized = self.handler.normalize_data(input_data)
        self.assertEqual(normalized["2024-12-24"]["sumMissedAttestations"], {'metric': None, 'per_val': None, 'attest_pct': None})

    def test_calculate_statistics(self):
        self.handler.node_data = {
            "2024-12-24": {
                "operator1": {
                    "avgInclusionDelay": {"metric": 1.05},
                    "avgValidatorEffectiveness":  {"metric": 94.4},
                    "validatorCount":  {"metric": 6}
                },
                "operator2": {
                    "avgInclusionDelay":  {"metric": 1.02},
                    "avgValidatorEffectiveness":  {"metric": 96.5},
                    "validatorCount":  {"metric": 6}
                }
            }
        }
        
        self.handler.get_statistics()
        
        stats = self.handler.node_stats["2024-12-24"]

        self.assertIn("avgInclusionDelay", stats)
        self.assertIn("avgValidatorEffectiveness", stats)
        
        # Test statistical calculations
        self.assertAlmostEqual(stats["avgInclusionDelay"]["metric"]["median"], 1.035, places=3)
        self.assertAlmostEqual(stats["avgValidatorEffectiveness"]["metric"]["median"], 95.45, places=2)

    def test_load_data(self):
        # Mock S3 responses
        self.mock_s3.get_dir_files.return_value = ["lido_csm/operator_data/CSM Operator 1"]
        self.mock_s3.get_data.return_value = self.test_data
        
        self.handler.load_data(self.mock_s3)
        
        # Verify data was loaded correctly
        self.assertIn("2024-12-24", self.handler.node_data)
        self.assertEqual(
            self.handler.node_data["2024-12-24"]["CSM Operator 1"]["validatorCount"]["metric"],
            6
        )

    def test_calculate_statistics_empty_data(self):
        self.handler.node_data = {}
        self.handler.get_statistics()
        self.assertEqual(self.handler.node_stats, {})

    def test_get_zscores_normal_case(self):
        self.handler.node_data = {
            "2024-12-24": {
                "operator1": {
                    "avgInclusionDelay": {"metric": 1.05},
                    "validatorCount": {"metric": 6}
                },
                "operator2": {
                    "avgInclusionDelay": {"metric": 1.02},
                    "validatorCount": {"metric": 8}
                }
            }
        }
        self.handler.node_stats = {
            "2024-12-24": {
                "avgInclusionDelay": {"metric": {"mean": 1.035, "std_dev": 0.015}},
                "validatorCount": {"metric": {"mean": 7, "std_dev": 1.0}}
            }
        }
        
        self.handler.get_zscores()
        self.assertAlmostEqual(
            self.handler.node_data["2024-12-24"]["operator1"]["avgInclusionDelay"]["zscore_metric"],
            (1.05 - 1.035) / 0.015,
            places=3
        )
        self.assertAlmostEqual(
            self.handler.node_data["2024-12-24"]["operator2"]["validatorCount"]["zscore_metric"],
            (8 - 7) / 1.0,
            places=1
        )

    def test_get_zscores_std_dev_zero(self):
        self.handler.node_data = {
            "2024-12-24": {
                "operator1": {"metric1": {"metric": 5}},
                "operator2": {"metric1": {"metric": 5}}
            }
        }
        self.handler.node_stats = {
            "2024-12-24": {"metric1": {"metric": {"mean": 5, "std_dev": 0.0}}}
        }
        
        self.handler.get_zscores()
        self.assertEqual(
           self.handler.node_data["2024-12-24"]["operator1"]["metric1"]["zscore_metric"],
            0.0
        )

    def test_get_zscores_missing_statistics(self):
        self.handler.node_data = {
            "2024-12-24": {
                "operator1": {"metric1": {"metric": 5}}
            }
        }
        self.handler.node_stats = {
            "2024-12-24": {"metric1": {"metric": {"mean": None, "std_dev": None}}}
        }
        
        self.handler.get_zscores()
        
        self.assertNotIn("metric1_zscore", self.handler.node_data["2024-12-24"]["operator1"])

    def test_get_zscores_handles_none_values(self):
        self.handler.node_data = {
            "2024-12-24": {
                "operator1": {"metric1": {"metric": None}}
            }
        }
        self.handler.node_stats = {
            "2024-12-24": {"metric1": {"metric":{"mean": 10, "std_dev": 2}}}
        }
        
        self.handler.get_zscores()
        
        self.assertNotIn("metric1_zscore", self.handler.node_data["2024-12-24"]["operator1"])

if __name__ == '__main__':
    unittest.main()
