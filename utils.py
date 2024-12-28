import statistics
from typing import List, Dict, Any

def extract_metric(operator_data: Dict[str, Any], metric: str) -> List[float]:
    """
    Extracts a specific metric from the operator's data for all dates.
    Skips None values.
    """
    return [
        day_data[metric]
        for day_data in operator_data.values()
        if metric in day_data and day_data[metric] is not None
    ]

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate median and standard deviation for a list of values.
    """
    if not values:
        return {'median': None, 'std_dev': None}
    
    return {
        'median': statistics.median(values),
        'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0
    }

def analyze_operator(operator_data: Dict[str, Any], metrics: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Analyze multiple metrics for a single operator.
    Returns a dictionary with metrics as keys and their statistics.
    """
    results = {}
    for metric in metrics:
        values = extract_metric(operator_data, metric)
        results[metric] = calculate_statistics(values)
    return results