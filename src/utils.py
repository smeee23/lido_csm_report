import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

ATTEST_METRICS = ["sumMissedAttestations", 
                 "sumCorrectHead",
                 "sumCorrectTarget",
                 "sumCorrectSource",
                 "sumWrongHeadVotes",
                 "sumWrongTargetVotes",
                 "sumLateTargetVotes",
                 "sumLateSourceVotes"]

OTHER_METRICS = ["validatorCount", 
                "totalUniqueAttestations",
                "avgAttesterEffectiveness",
                "sumInclusionDelay",
                "sumMissedSyncSignatures",
                "sumSyncSignatureCount",
                "avgInclusionDelay",
                "avgUptime",
                "avgCorrectness",
                "avgProposerEffectiveness",
                "avgValidatorEffectiveness"]
 

def create_output_file(id, variable, date="", type_plot="histogram", module="CSM", file_name=None):

    if isinstance(date, list) and len(date) > 1:
        date = f"{date[0]}_{date[len(date)-1]}"

    # Define the output file path using os.path.join
    if file_name is None:
       file_name = f"{variable}_{date}.png" 
    output_file = os.path.join("reports", module, str(id), type_plot, file_name)
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    return output_file

def format_op_ids(operator_ids):
    if len(operator_ids) == 1:
        return str(operator_ids[0])

    s = ""
    for id in operator_ids:
        s = f"{s}_{id}"
    
    return s

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

def find_date_groups(dates_dict):
    # Convert string dates to datetime objects and sort in descending order
    sorted_dates = sorted([datetime.strptime(date, "%Y-%m-%d") for date in dates_dict.keys()], reverse=True)
    
    def find_sequential_group(target_length):
        """Find a group of sequential dates of target_length starting from the most recent date."""
        group = [sorted_dates[0]]
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i - 1] - sorted_dates[i]).days == 1:
                group.append(sorted_dates[i])
                if len(group) == target_length:
                    return [date.strftime("%Y-%m-%d") for date in group]
        return None
    
    result = {}
    for length in [3, 7, 30]:
        group = find_sequential_group(length)
        if group:
            result[length] = group
    
    return result
