import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import numpy as np
import re

def get_syn_std_dev(stat, id):
    if "CSM Operator" in id: 
        data = csm_stats
        if "sum" in stat:
            deviation_constant = 0.1
        else:
            deviation_constant = 0.15
    elif "- Lido SimpleDVT Module" in id:
        data = sdvt_stats
        if "sum" in stat:
            deviation_constant = 0.07
        else:
            deviation_constant = 0.15
    else:
        data = curated_stats
        if "sum" in stat:
            deviation_constant = 0.005
        else:
            deviation_constant = 0.1

    if stat in data:
        return data[stat]["stddev"] * deviation_constant
    else:
        return None
   
def create_output_file(id, variable, date="", type_report="histogram", module="CSM", file_name=None, ext="png", dist_type=None):

    if isinstance(date, list) and len(date) > 1:
        date = f"{date[0]}_{date[len(date)-1]}"

    # Define the output file path using os.path.join
    if file_name is None:
       if dist_type:
           file_name = f"{variable}_{date}_{dist_type}.{ext}" 
       else: 
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
    for length in [3, 5, 7, 30]:
        group = find_sequential_group(length)
        if group:
            result[length] = group
    
    return result

def get_average_ratings_for_dates(data, variable, operator_ids, variant="per_val", date=None):
    highlighted_ratings = []
    other_ratings = []
    operator_counts = {}
    operator_sums = {}

    # If date is None, use all available dates in the data
    # exclude compound dates e.g. 2024-12-25_2024-12-27
    valid_dates = [d for d in list(data.keys()) if "_" not in d]
    if date is None: dates = valid_dates
    else: dates = date

    for current_date in dates:
        if current_date in data and "_" not in current_date:
            for operator, metrics in data[current_date].items():
                if variable in metrics and metrics[variable][variant] is not None:
                    if operator not in operator_counts:
                        operator_counts[operator] = 0
                        operator_sums[operator] = 0

                    operator_counts[operator] += 1
                    operator_sums[operator] += metrics[variable][variant]

    # Calculate averages
    for operator in operator_counts:
        avg = operator_sums[operator] / operator_counts[operator]
        if any(f"Operator {id} -" in operator for id in operator_ids):
            highlighted_ratings.append(avg)
        else:
            other_ratings.append(avg)
    return highlighted_ratings, other_ratings, dates

def format_title(metric, date, graph_type="Distribution"):
    # Remove the first 6 characters if the string starts with "perVal"
    if metric.startswith("perVal"):
        metric = metric[6:]
    
    # Add a space before each capital letter
    formatted_string = generate_spaces(metric)
    
    if date is None:
        date = ""
    elif isinstance(date, list) and len(date) > 1:
        date = f"{len(date)}day MVA {date[len(date)-1]}"
    elif "_" in date:
        date = date.replace("_", " - ")
    

    return f"{formatted_string.replace("avg", "Average")} {graph_type} {date}" 

def format_label(metric):
    if metric.startswith("perVal"):
        new_metric = metric[6:]
    else:
        new_metric = metric
    # Add a space before each capital letter
    formatted_string = generate_spaces(new_metric)
    
    if metric.startswith("perVal"):
        return f"{formatted_string} Per Validator"
    return formatted_string 

def generate_spaces(s):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', s).replace("avg", "").replace("sum", "")

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

DESCRIPTIONS = {
    "sumWrongHeadVotes": {"variant": "per_val", "desc" : "A wrong head vote in Ethereum consensus refers to a validator incorrectly voting for a block that is not the canonical head of the chain according to the LMD-GHOST fork-choice rule. Validators are expected to vote for the block with the highest accumulated attestations as the chain’s head. Wrong head votes can result from network delays, client issues, or outdated views of the chain. Frequent wrong head votes reduce validator rewards and can degrade network performance by delaying finality."},
    "avgValidatorEffectiveness": {"variant": "metric","desc" : "A measure of the average performance of a validator across key consensus duties, such as proposing blocks and attesting correctly. A higher rating indicates that the validator consistently participates in securing the network and follows the protocol rules effectively. This metric helps assess the reliability and efficiency of a validator, with poor effectiveness typically resulting in lower rewards and a negative impact on the network’s overall health."},
    "avgInclusionDelay": {"variant": "metric","desc" : "The average of the distance between the slot a validator’s attestation is expected by the network and the slot the attestation is actually included on-chain. Lower inclusion delay indicates that a validator’s attestations are being included quickly, maximizing rewards and contributing effectively to consensus. High inclusion delay can result from network latency, poor relay performance, or delayed broadcasting, leading to reduced rewards and slower finalization of the chain. This metric is crucial for evaluating a validator’s responsiveness and network efficiency."},
    "sumWrongTargetVotes": {"variant": "per_val","desc" : "A wrong target vote occurs when a validator attests to an incorrect target checkpoint for a given epoch. Each epoch has a target checkpoint, and validators are expected to vote for the correct target to ensure the network's security and efficiency. Incorrect target votes can result from network delays, synchronization issues, or misconfigurations, leading to penalties for the validator and potentially affecting the network's finality."},
    "sumMissedAttestations": {"variant": "per_val","desc" : "Missed attestations refer to situations where an Ethereum validator fails to submit an attestation for a block they are supposed to attest to during a given epoch. Attestations are essential for reaching consensus and finalizing blocks, and missing them can result from network issues, poor validator performance, or misconfigurations. Missed attestations negatively affect a validator's rewards and can lead to penalties. High rates of missed attestations reduce the validator's reliability and can slow down the finalization process, impacting the overall network health."},
    "sumLateSourceVotes": {"variant": "per_val","desc" : "A late source vote occurs when a validator attests to a source checkpoint after the optimal time window, which is within 1 to 5 slots after the checkpoint's creation. Validators are expected to submit their source votes promptly to maintain network efficiency and security. Late source votes can result from network delays, synchronization issues, or misconfigurations. While there is no direct penalty for a late source vote, it can lead to missed target votes, which are penalized."},
    "avgCorrectness": {"variant": "metric","desc" : "A measure of how many times a validator or entity has attested correctly in their target and head vote duties. The average between Target and Header accuracy. A higher rating indicates that the validator consistently follows protocol guidelines, contributing to network security and efficiency. This metric is essential for assessing a validator's reliability and performance within the Ethereum ecosystem."},
    "avgAttesterEffectiveness": {"variant": "metric","desc" : "A measure of how effectively an Ethereum validator performs its attestation duties, which are crucial for network consensus. Validators are expected to submit accurate and timely attestations, including source, target, and head votes, to support the chain's finality and security. High attester effectiveness indicates that a validator consistently follows protocol rules, contributing to network stability and earning rewards. Conversely, low effectiveness can result from missed or incorrect attestations, leading to penalties and reduced rewards."}
}

LIDO_CURATED = [
    "ParaFi Technologies", 
    "Gateway.fm", 
    "Attestant", 
    "Ebunker", 
    "Kukis Global", 
    "Galaxy", 
    "RockawayX Infra", 
    "Nethermind", 
    "Stakely", 
    "Blockdaemon", 
    "ChainSafe", 
    "A41", 
    "Consensys", 
    "Develp GmbH", 
    "HashKey Cloud", 
    "Sigma Prime", 
    "RockLogic GmbH", 
    "Prysm Team at Offchain Labs", 
    "BridgeTower", 
    "Launchnodes", 
    "Stakin", 
    "Simply Staking", 
    "SenseiNode", 
    "ChainLayer", 
    "InfStones", 
    "P2P.ORG - P2P Validator", 
    "Blockscape", 
    "Allnodes", 
    "Everstake", 
    "RockX", 
    "Kiln", 
    "Chorus One", 
    "Staking Facilities", 
    "Stakefish", 
    "DSRV", 
    "Figment"
]

LIDO_SDVT = [
    "Obol - Divine Dragon", "Obol - Cunning Chimera", "Obol - Arctic Amarok",
    "Obol - Bold Banshee", "Obol - Ethereal Elf", "SSV - Arid Anubis",
    "SSV - Blazing Basilisk", "SSV - Celestial Cyclops", "SSV - Enigmatic Ent",
    "SSV - Dreamy Draugr", "Obol - Lustrous Leopard", "Obol - Jubilant Jackrabbit",
    "Obol - Covert Cougar", "Obol - Harmonious Hawk", "Obol - Dazzling Duck",
    "Obol - Knightly Kinkajou", "Obol - Frolicsome Frog", "Obol - Genteel Giraffe",
    "Obol - Enigmatic Elk", "Obol - Azure Albatross", "Obol - Bountiful Bison",
    "Obol - Ingenious Ibis", "SSV - Blissful Bear", "SSV - Curious Coyote",
    "SSV - Agile Antelope", "SSV - Ethereal Elephant", "SSV - Humble Hummingbird",
    "SSV - Graceful Gazelle", "SSV - Delightful Dolphin", "SSV - Flirtatious Flamingo",
    "Obol - Quixotic Quail", "Obol - Tranquil Turtle", "Obol - Xeric Xiphosuran", 
    "Obol - Radiant Raccoon", "Obol - Unfettered Urial", "Obol - Observant Octopus", 
    "SSV - Lively Lynx", "Obol - Zephyr Zorilla", "Obol - Yielding Yellowthroat", 
    "Obol - Majestic Moose", "Obol - Nurturing Narwhal", "Obol - Serendipitous Shark", 
    "SSV - Joyful Jaguar", "Obol - Prancing Peacock", "Obol - Whistling Wolf",
    "SSV - Intrepid Impala", "SSV - Keen Koala", "Obol - Vivacious Viper", 
    "SSV - Unique Unicorn", "SSV - Optimistic Orca", "SSV - Splendid Swan", 
    "SSV - Noble Newt", "SSV - Thoughtful Tiger", "SSV - Mysterious Manta", 
    "SSV - Playful Penguin", "SSV - Quiet Quetzal", "SSV - Resilient Rabbit"
]

csm_stats = {'validatorCount': {'mean': np.float64(926.8317853457172), 'stddev': np.float64(2549.0410608983275)}, 'totalUniqueAttestations': {'mean': np.float64(208371.14138286893), 'stddev': np.float64(573132.6319720185)}, 'sumMissedAttestations': {'mean': np.float64(97.74406604747162), 'stddev': np.float64(450.2020603839414)}, 'sumMissedSyncSignatures': {'mean': np.float64(609.0873015873016), 'stddev': np.float64(560.4238684401837)}, 'sumCorrectHead': {'mean': np.float64(205171.5944272446), 'stddev': np.float64(564371.7531902685)}, 'sumCorrectTarget': {'mean': np.float64(208201.47368421053), 'stddev': np.float64(572669.6567495634)}, 'sumCorrectSource': {'mean': np.float64(208248.26109391125), 'stddev': np.float64(572796.2746984683)}, 'sumWrongHeadVotes': {'mean': np.float64(1795.4278296988577), 'stddev': np.float64(6725.952638686401)}, 'sumWrongTargetVotes': {'mean': np.float64(170.72481827622013), 'stddev': np.float64(554.9511207679691)}, 'sumLateTargetVotes': {'mean': np.float64(0.0), 'stddev': np.float64(0.0)}, 'sumLateSourceVotes': {'mean': np.float64(123.64589823468329), 'stddev': np.float64(469.9798910318635)}, 'avgAttesterEffectiveness': {'mean': np.float64(95.99654139400671), 'stddev': np.float64(9.115443801314502)}, 'sumInclusionDelay': {'mean': np.float64(211970.44582043344), 'stddev': np.float64(583039.3067991949)}, 'sumSyncSignatureCount': {'mean': np.float64(3235.061919504644), 'stddev': np.float64(9994.88528021993)}, 'avgInclusionDelay': {'mean': np.float64(1.0276589255322583), 'stddev': np.float64(0.05354837967099608)}, 'avgUptime': {'mean': np.float64(0.9919540867119517), 'stddev': np.float64(0.08114573681393693)}, 'avgCorrectness': {'mean': np.float64(0.9851324110380308), 'stddev': np.float64(0.07869129940787745)}, 'avgProposerEffectiveness': {'mean': np.float64(99.34639065558302), 'stddev': np.float64(7.072006991523501)}, 'avgValidatorEffectiveness': {'mean': np.float64(96.00035253869663), 'stddev': np.float64(9.115678891446185)}}
sdvt_stats = {'validatorCount': {'mean': np.float64(926.8317853457172), 'stddev': np.float64(2549.0410608983275)}, 'totalUniqueAttestations': {'mean': np.float64(208371.14138286893), 'stddev': np.float64(573132.6319720185)}, 'sumMissedAttestations': {'mean': np.float64(97.74406604747162), 'stddev': np.float64(450.2020603839414)}, 'sumMissedSyncSignatures': {'mean': np.float64(609.0873015873016), 'stddev': np.float64(560.4238684401837)}, 'sumCorrectHead': {'mean': np.float64(205171.5944272446), 'stddev': np.float64(564371.7531902685)}, 'sumCorrectTarget': {'mean': np.float64(208201.47368421053), 'stddev': np.float64(572669.6567495634)}, 'sumCorrectSource': {'mean': np.float64(208248.26109391125), 'stddev': np.float64(572796.2746984683)}, 'sumWrongHeadVotes': {'mean': np.float64(1795.4278296988577), 'stddev': np.float64(6725.952638686401)}, 'sumWrongTargetVotes': {'mean': np.float64(170.72481827622013), 'stddev': np.float64(554.9511207679691)}, 'sumLateTargetVotes': {'mean': np.float64(0.0), 'stddev': np.float64(0.0)}, 'sumLateSourceVotes': {'mean': np.float64(123.64589823468329), 'stddev': np.float64(469.9798910318635)}, 'avgAttesterEffectiveness': {'mean': np.float64(95.99654139400671), 'stddev': np.float64(9.115443801314502)}, 'sumInclusionDelay': {'mean': np.float64(211970.44582043344), 'stddev': np.float64(583039.3067991949)}, 'sumSyncSignatureCount': {'mean': np.float64(3235.061919504644), 'stddev': np.float64(9994.88528021993)}, 'avgInclusionDelay': {'mean': np.float64(1.0276589255322583), 'stddev': np.float64(0.05354837967099608)}, 'avgUptime': {'mean': np.float64(0.9919540867119517), 'stddev': np.float64(0.08114573681393693)}, 'avgCorrectness': {'mean': np.float64(0.9851324110380308), 'stddev': np.float64(0.07869129940787745)}, 'avgProposerEffectiveness': {'mean': np.float64(99.34639065558302), 'stddev': np.float64(7.072006991523501)}, 'avgValidatorEffectiveness': {'mean': np.float64(96.00035253869663), 'stddev': np.float64(9.115678891446185)}}
curated_stats = {'validatorCount': {'mean': np.float64(926.8317853457172), 'stddev': np.float64(2549.0410608983275)}, 'totalUniqueAttestations': {'mean': np.float64(208371.14138286893), 'stddev': np.float64(573132.6319720185)}, 'sumMissedAttestations': {'mean': np.float64(97.74406604747162), 'stddev': np.float64(450.2020603839414)}, 'sumMissedSyncSignatures': {'mean': np.float64(609.0873015873016), 'stddev': np.float64(560.4238684401837)}, 'sumCorrectHead': {'mean': np.float64(205171.5944272446), 'stddev': np.float64(564371.7531902685)}, 'sumCorrectTarget': {'mean': np.float64(208201.47368421053), 'stddev': np.float64(572669.6567495634)}, 'sumCorrectSource': {'mean': np.float64(208248.26109391125), 'stddev': np.float64(572796.2746984683)}, 'sumWrongHeadVotes': {'mean': np.float64(1795.4278296988577), 'stddev': np.float64(6725.952638686401)}, 'sumWrongTargetVotes': {'mean': np.float64(170.72481827622013), 'stddev': np.float64(554.9511207679691)}, 'sumLateTargetVotes': {'mean': np.float64(0.0), 'stddev': np.float64(0.0)}, 'sumLateSourceVotes': {'mean': np.float64(123.64589823468329), 'stddev': np.float64(469.9798910318635)}, 'avgAttesterEffectiveness': {'mean': np.float64(95.99654139400671), 'stddev': np.float64(9.115443801314502)}, 'sumInclusionDelay': {'mean': np.float64(211970.44582043344), 'stddev': np.float64(583039.3067991949)}, 'sumSyncSignatureCount': {'mean': np.float64(3235.061919504644), 'stddev': np.float64(9994.88528021993)}, 'avgInclusionDelay': {'mean': np.float64(1.0276589255322583), 'stddev': np.float64(0.05354837967099608)}, 'avgUptime': {'mean': np.float64(0.9919540867119517), 'stddev': np.float64(0.08114573681393693)}, 'avgCorrectness': {'mean': np.float64(0.9851324110380308), 'stddev': np.float64(0.07869129940787745)}, 'avgProposerEffectiveness': {'mean': np.float64(99.34639065558302), 'stddev': np.float64(7.072006991523501)}, 'avgValidatorEffectiveness': {'mean': np.float64(96.00035253869663), 'stddev': np.float64(9.115678891446185)}}
