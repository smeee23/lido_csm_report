import unittest
from utils import extract_metric, calculate_statistics, analyze_operator

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            "2024-12-24": {
                "avgInclusionDelay": 1.05,
                "avgValidatorEffectiveness": 94.4
            },
            "2024-12-25": {
                "avgInclusionDelay": 1.02,
                "avgValidatorEffectiveness": 96.5
            }
        }

    def test_extract_metric(self):
        values = extract_metric(self.test_data, "avgInclusionDelay")
        self.assertEqual(len(values), 2)
        self.assertAlmostEqual(values[0], 1.05)
        self.assertAlmostEqual(values[1], 1.02)

    def test_extract_metric_missing_data(self):
        data = {
            "2024-12-24": {"metric1": 1.0},
            "2024-12-25": {"metric1": None},
            "2024-12-26": {}
        }
        values = extract_metric(data, "metric1")
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0], 1.0)

    def test_calculate_statistics(self):
        values = [1.0, 2.0, 3.0, 4.0]
        stats = calculate_statistics(values)
        
        self.assertEqual(stats["median"], 2.5)
        self.assertAlmostEqual(stats["std_dev"], 1.2909944487358056)

    def test_calculate_statistics_empty_list(self):
        stats = calculate_statistics([])
        self.assertIsNone(stats["median"])
        self.assertIsNone(stats["std_dev"])

    def test_analyze_operator(self):
        metrics = ["avgInclusionDelay", "avgValidatorEffectiveness"]
        analysis = analyze_operator(self.test_data, metrics)
        
        self.assertIn("avgInclusionDelay", analysis)
        self.assertIn("avgValidatorEffectiveness", analysis)
        
        self.assertAlmostEqual(analysis["avgInclusionDelay"]["median"], 1.035)
        self.assertAlmostEqual(analysis["avgValidatorEffectiveness"]["median"], 95.45)

if __name__ == '__main__':
    unittest.main()
