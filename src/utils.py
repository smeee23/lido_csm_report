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

SUMS = []

DESCRIPTIONS = {
    "sumWrongHeadVotes": "A wrong head vote in Ethereum consensus refers to a validator incorrectly voting for a block that is not the canonical head of the chain according to the LMD-GHOST fork-choice rule. Validators are expected to vote for the block with the highest accumulated attestations as the chain’s head. Wrong head votes can result from network delays, client issues, or outdated views of the chain. Frequent wrong head votes reduce validator rewards and can degrade network performance by delaying finality.",
    "avgValidatorEffectiveness": "A measure of the average performance of a validator across key consensus duties, such as proposing blocks and attesting correctly. A higher rating indicates that the validator consistently participates in securing the network and follows the protocol rules effectively. This metric helps assess the reliability and efficiency of a validator, with poor effectiveness typically resulting in lower rewards and a negative impact on the network’s overall health.",
    "avgInclusionDelay": "The average of the distance between the slot a validator’s attestation is expected by the network and the slot the attestation is actually included on-chain. Lower inclusion delay indicates that a validator’s attestations are being included quickly, maximizing rewards and contributing effectively to consensus. High inclusion delay can result from network latency, poor relay performance, or delayed broadcasting, leading to reduced rewards and slower finalization of the chain. This metric is crucial for evaluating a validator’s responsiveness and network efficiency.",
    "sumWrongTargetVotes": "A wrong target vote occurs when a validator attests to an incorrect target checkpoint for a given epoch. Each epoch has a target checkpoint, and validators are expected to vote for the correct target to ensure the network's security and efficiency. Incorrect target votes can result from network delays, synchronization issues, or misconfigurations, leading to penalties for the validator and potentially affecting the network's finality.",
    #"sumMissedAttestations": "Missed attestations refer to situations where an Ethereum validator fails to submit an attestation for a block they are supposed to attest to during a given epoch. Attestations are essential for reaching consensus and finalizing blocks, and missing them can result from network issues, poor validator performance, or misconfigurations. Missed attestations negatively affect a validator's rewards and can lead to penalties. High rates of missed attestations reduce the validator's reliability and can slow down the finalization process, impacting the overall network health.",
    "sumLateSourceVotes": "A late source vote occurs when a validator attests to a source checkpoint after the optimal time window, which is within 1 to 5 slots after the checkpoint's creation. Validators are expected to submit their source votes promptly to maintain network efficiency and security. Late source votes can result from network delays, synchronization issues, or misconfigurations. While there is no direct penalty for a late source vote, it can lead to missed target votes, which are penalized.",
    "avgCorrectness": "A measure of how many times a validator or entity has attested correctly in their target and head vote duties. The average between Target and Header accuracy. A higher rating indicates that the validator consistently follows protocol guidelines, contributing to network security and efficiency. This metric is essential for assessing a validator's reliability and performance within the Ethereum ecosystem.",
    "avgAttesterEffectiveness": "A measure of how effectively an Ethereum validator performs its attestation duties, which are crucial for network consensus. Validators are expected to submit accurate and timely attestations, including source, target, and head votes, to support the chain's finality and security. High attester effectiveness indicates that a validator consistently follows protocol rules, contributing to network stability and earning rewards. Conversely, low effectiveness can result from missed or incorrect attestations, leading to penalties and reduced rewards."
} 

def create_output_file(id, variable, date="", type_report="histogram", module="CSM", file_name=None, ext="png"):

    if isinstance(date, list) and len(date) > 1:
        date = f"{date[0]}_{date[len(date)-1]}"

    # Define the output file path using os.path.join
    if file_name is None:
       file_name = f"{variable}_{date}.{ext}" 
    output_file = os.path.join("reports", module, str(id), type_report, file_name)
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
