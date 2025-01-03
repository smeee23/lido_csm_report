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
            }
        }
        
        normalized = self.handler.normalize_data(input_data)
        
        self.assertEqual(normalized["2024-12-24"]["validatorCount"], 10)
        self.assertEqual(normalized["2024-12-24"]["sumMissedAttestations"], 50)
        self.assertEqual(normalized["2024-12-24"]["sumInclusionDelay"], 1000)
        self.assertEqual(normalized["2024-12-24"]["perValMissedAttestations"], 5.0)
        self.assertEqual(normalized["2024-12-24"]["perValInclusionDelay"], 100.0)

    def test_normalize_data_handles_none(self):
        input_data = {
            "2024-12-24": {
                "validatorCount": 10,
                "sumMissedAttestations": None,
            }
        }
        
        normalized = self.handler.normalize_data(input_data)
        self.assertIsNone(normalized["2024-12-24"]["perValMissedAttestations"])

    def test_calculate_statistics(self):
        self.handler.node_data = {
            "2024-12-24": {
                "operator1": {
                    "avgInclusionDelay": 1.05,
                    "avgValidatorEffectiveness": 94.4,
                    "validatorCount": 6
                },
                "operator2": {
                    "avgInclusionDelay": 1.02,
                    "avgValidatorEffectiveness": 96.5,
                    "validatorCount": 6
                }
            }
        }
        
        self.handler.calculate_statistics()
        
        stats = self.handler.node_stats["2024-12-24"]
        self.assertIn("avgInclusionDelay", stats)
        self.assertIn("avgValidatorEffectiveness", stats)
        
        # Test statistical calculations
        self.assertAlmostEqual(stats["avgInclusionDelay"]["median"], 1.035, places=3)
        self.assertAlmostEqual(stats["avgValidatorEffectiveness"]["median"], 95.45, places=2)

    def test_load_data(self):
        # Mock S3 responses
        self.mock_s3.get_dir_files.return_value = ["lido_csm/operator_data/CSM Operator 1"]
        self.mock_s3.get_data.return_value = self.test_data
        
        self.handler.load_data(self.mock_s3)
        
        # Verify data was loaded correctly
        self.assertIn("2024-12-24", self.handler.node_data)
        self.assertEqual(
            self.handler.node_data["2024-12-24"]["CSM Operator 1"]["validatorCount"],
            6
        )

    def test_calculate_statistics_empty_data(self):
        self.handler.node_data = {}
        self.handler.calculate_statistics()
        self.assertEqual(self.handler.node_stats, {})

if __name__ == '__main__':
    unittest.main()
