from logger_config import logger
from GaitKeeper import GaitKeeper
import traceback
import time
import statistics
import numpy as np
import re

class DataHandler:
    def __init__(self):
        self.agg_data = {}
        self.node_data = {}
        self.node_stats = {}  

    def load_data(self, s3):
        files = s3.get_dir_files("lido_csm/operator_data/")
        for key in files:
            try:
                op_data = self.normalize_data(s3.get_data(key))
                id = key.split('/')[2]
                if "CSM Operator" in id: 
                    data = self.node_data
                else:
                    data = self.agg_data

                for date in op_data:
                    if date not in data:
                        data[date] = {}
                    data[date][id] = op_data[date]

            except Exception as e:
                traceback.print_exc()
                logger.error(f"An error occurred in load_data: {e}")
    
    def normalize_data(self, data):
        normalized_data = {}
        for date, values in data.items():
            normalized_entry = {}
            num_vals = values["validatorCount"]
            total_attest = values["totalUniqueAttestations"]
            for k, v in values.items():
               
                normalized_entry[k] = v
                if "sum" in k:
                    per_val = k.replace("sum", "perVal")
                    pct = k.replace("sum", "pct")
                    
                    if v is None:
                        normalized_entry[per_val] = None
                    elif v == 0:
                        normalized_entry[per_val] = 0.0
                        normalized_entry[k] = 0.0
                    else:
                        normalized_entry[per_val] = v / num_vals
                        normalized_entry[pct] = self.calc_percent(stat=v, total_attest=total_attest)
            normalized_data[date] = normalized_entry
        return normalized_data

    def get_statistics(self):
        #stats_per_date = {}
        
        for date, operators in self.node_data.items():
            self.node_stats[date] = {}
            
            # Extract all metrics
            all_metrics = {}
            for operator, metrics in operators.items():
                for metric, value in metrics.items():
                    if (
                        isinstance(value, (int, float)) and 
                        value is not None and
                        not any(keyword in metric for keyword in ["sum", "total", "Slot", "Epoch"])
                        ):
                            if metric not in all_metrics:
                                all_metrics[metric] = []
                            all_metrics[metric].append(value)
            
            # Calculate statistics for each metric
            for metric, values in all_metrics.items():

                valid_values = [v for v in values if v is not None]
                try:
                    if valid_values:
                        median = statistics.median(valid_values)
                        mean = statistics.mean(valid_values)
                        mode = statistics.mode(valid_values) if len(set(valid_values)) > 1 else None
                        std_dev = np.std(valid_values)
                    else:
                        median = mean = mode = std_dev = None
                    
                    # Store the statistics
                    self.node_stats[date][metric] = {
                        'median': median,
                        'mean': mean,
                        'mode': mode,
                        'std_dev': std_dev,
                    }
                except statistics.StatisticsError:
                    # In case of any errors with statistics calculation (e.g., no valid values)
                    self.node_stats[date][metric] = {
                        'median': None,
                        'mean': None,
                        'mode': None,
                        'std_dev': None,
                    }

    def get_zscores(self):
        for date, operators in list(self.node_data.items()):  # Create a list copy of items to iterate
            for operator, metrics in list(operators.items()):  # Create a list copy of operator items
                for metric, value in list(metrics.items()):  # Create a list copy of metric items
                    if date in self.node_stats and value is not None:
                        if metric in self.node_stats[date]:
                            try:
                                std_dev = self.node_stats[date][metric]["std_dev"]
                                mean = self.node_stats[date][metric]["mean"]
                                if std_dev != 0.0:
                                    zscore = (value - mean) / std_dev
                                    label = f"{metric}_zscore"
                                    self.node_data[date][operator][label] = zscore
                            except Exception as e:
                                traceback.print_exc()
                                logger.error(f"An error occurred in zscore for {operator} {metric}: {e}")


    def calc_percent(self, stat, total_attest):
        if total_attest == 0:
            return float('nan')
        return (stat / total_attest) * 100 

    def calc_zscore(self, value, mean, std_dev):
        return (value - mean) / std_dev