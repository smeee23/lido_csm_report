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

    def load_data(self, files, s3):
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
            for k, v in values.items():
               
                normalized_entry[k] = v
                if any(keyword in k for keyword in ["sum", "total"]):
                    title = re.sub(r'\b(sum|total)\b', 'avg', k)
                    if v is None:
                        normalized_entry[title] = None
                    elif v == 0:
                        normalized_entry[title] = 0.0
                        normalized_entry[k] = 0.0
                    else:
                        normalized_entry[title] = v / num_vals
            normalized_data[date] = normalized_entry
        return normalized_data

    def calculate_statistics(self):
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