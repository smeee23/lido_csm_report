from logger_config import logger
from utils import ATTEST_METRICS, OTHER_METRICS, find_date_groups, get_syn_std_dev
import traceback
import time
import statistics
import numpy as np
import re
import pandas

class DataHandler:
    def __init__(self):
        self.agg_data = {}
        self.node_data = {}
        self.curated_module_data = {}
        self.sdvt_data = {}
        self.node_stats = {}
        self.df = None

    def create_df(self):
        rows = []
        dates = set()
        for data in [self.node_data,self.curated_module_data, self.sdvt_data]:
            for date, operators in data.items():
                dates.add(date)
                for operator, stats in operators.items():
                    row = {"date": date, "operator": operator}
                    for variable, values in stats.items():
                        for metric, value in values.items():
                            row[f"{variable}_{metric}"] = value
                    rows.append(row)
        # Create DataFrame
        df = pandas.DataFrame(rows)
        
        # Set MultiIndex using date and operator
        df = df.set_index(['date', 'operator'])
        df = df.sort_index()
        pandas.set_option('display.max_columns', None)

        csm_df = df[df.index.get_level_values('operator').str.contains("CSM Operator")]
        sdvt_df = df[df.index.get_level_values('operator').str.contains("- Lido SimpleDVT Module")]
        pattern = r'.*- Lido$'  # Regex pattern
        curated_df = df[df.index.get_level_values('operator').str.contains(pattern, regex=True)]

        synthetic = []
        for col in [*ATTEST_METRICS, *OTHER_METRICS]:
            synthetic.append(f"{col}_metric")

        csm_metric_columns = [col for col in csm_df.columns if col in synthetic]
        stats = {
            col[:-7]: {
                'mean': df[col].mean(),
                'stddev': df[col].std()
            }
            for col in csm_metric_columns
        }

        sdvt_metric_columns = [col for col in sdvt_df.columns if col in synthetic]
        stats = {
            col[:-7]: {
                'mean': df[col].mean(),
                'stddev': df[col].std()
            }
            for col in sdvt_metric_columns
        }

        curated_metric_columns = [col for col in curated_df.columns if col in synthetic]
        stats = {
            col[:-7]: {
                'mean': df[col].mean(),
                'stddev': df[col].std()
            }
            for col in curated_metric_columns
        }
        self.df = df        

    def load_data(self, s3):
        files = s3.get_dir_files("lido_csm/operator_data/")
        for key in files:
            try:
                s3_data = s3.get_data(key)
                id = key.split('/')[2]
                op_data = self.normalize_data(s3_data)
                
                if "CSM Operator" in id: 
                    data = self.node_data
                elif "- Lido SimpleDVT Module" in id:
                    data = self.sdvt_data
                elif "- Lido" in id:
                    data = self.curated_module_data
                else:
                    #for demo date match remove in prod
                    if "2025-01-11" in op_data:
                        op_data['2025-01-12'] = op_data["2025-01-11"]
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
            if date not in ["2024-12-26", "2024-12-25", 
                            "2024-12-24", "2025-01-17", 
                            "2025-01-18"]:
                normalized_entry = {}
                num_vals = values.get("validatorCount", 0)
                total_attest = values.get("totalUniqueAttestations", 0)
                for k, v in values.items():
                    if k not in ["startSlot", "endSlot", "startEpoch", "endEpoch"]:
                        normalized_entry[k] = {"metric": v}
                        if "sum" in k:                                     
                            if v is None:
                                normalized_entry[k]["per_val"] = None
                                if k in ATTEST_METRICS:
                                    normalized_entry[k]["attest_pct"] = None
                            elif v == 0:
                                normalized_entry[k] = {"metric": 0.0, "per_val": 0.0}
                                if k in ATTEST_METRICS:
                                    normalized_entry[k]["attest_pct"] = 0.0
                            else:
                                normalized_entry[k]["per_val"] = v / num_vals
                                if k in ATTEST_METRICS:
                                    normalized_entry[k]["attest_pct"] = self.calc_percent(stat=v, total_attest=total_attest) 
                entry_date = date
                #for demo dates to match remove in prod
                if date == "2024-12-27": 
                    entry_date = "2025-01-16"
                normalized_data[entry_date] = normalized_entry
        return normalized_data

    def get_statistics(self, module="csm"):
        #stats_per_date = {}
        data = {}
        if module == "csm":
            data = self.node_data
        elif module == "curated":
            data = self.curated_module_data
        elif module == "sdvt":
            data = self.sdvt_data

        for date, operators in data.items():
            self.node_stats[date] = {}
            
            # Extract metrics
            all_metrics = {metric: {} for metric in set(ATTEST_METRICS + OTHER_METRICS)}
            for operator, variables in operators.items():
                for item, metrics in variables.items():
                    for metric, value in metrics.items():
                        if (
                            isinstance(value, (int, float)) and 
                            value is not None and
                            item in all_metrics
                            ):
                                if metric not in all_metrics[item]:
                                    all_metrics[item][metric]= []
                                all_metrics[item][metric].append(value)
            
            # Calculate statistics for each metric
            for metric, values in all_metrics.items():
                self.node_stats[date][metric] = {}
                for variable_name, metric_derivs in values.items():
                    valid_values = [v for v in metric_derivs if v is not None]
                    try:
                        if valid_values:
                            median = np.median(valid_values)
                            mean = np.mean(valid_values)
                            mode = statistics.mode(valid_values) if len(set(valid_values)) > 1 else None
                            std_dev = np.std(valid_values)
                        else:
                            median = mean = mode = std_dev = None
                        
                        # Store the statistics
                        self.node_stats[date][metric][variable_name] = {
                            'median': median,
                            'mean': mean,
                            'mode': mode,
                            'std_dev': std_dev,
                        }
                    except Exception as e:
                        # In case of any errors with statistics calculation (e.g., no valid values)
                        self.node_stats[date][metric][variable_name]  = {
                            'median': None,
                            'mean': None,
                            'mode': None,
                            'std_dev': None,
                        }

    def get_zscores(self, module="csm"):
        data = {}
        if module == "csm":
            data = self.node_data
        elif module == "curated":
            data = self.curated_module_data
        elif module == "sdvt":
            data = self.sdvt_data

        for date, operators in list(data.items()):  
            
            for operator, metrics in list(operators.items()):  
                for metric, value in list(metrics.items()): 
                    if date in self.node_stats and value['metric'] is not None:
                        if metric in self.node_stats[date]:
                            try:
                                if "per_val" in value:
                                    std_dev_per_val = self.node_stats[date][metric]["per_val"]["std_dev"]
                                    mean_per_val = self.node_stats[date][metric]["per_val"]["mean"]
                                    zscore = self.calc_zscore(value["per_val"], mean_per_val, std_dev_per_val)
                                    label = "zscore_per_val"
                                    data[date][operator][metric][label] = zscore
                                    if "attest_pct" in value:
                                        std_dev_pct = self.node_stats[date][metric]["attest_pct"]["std_dev"]
                                        mean_pct = self.node_stats[date][metric]["attest_pct"]["mean"]
                                        zscore = self.calc_zscore(value["attest_pct"], mean_pct, std_dev_pct)
                                        label = "zscore_attest_pct"
                                        data[date][operator][metric][label] = zscore
                                else:
                                    std_dev = self.node_stats[date][metric]["metric"]["std_dev"]
                                    mean = self.node_stats[date][metric]["metric"]["mean"]
                                    zscore = self.calc_zscore(value["metric"], mean, std_dev)
                                    label = "zscore_metric"
                                    data[date][operator][metric][label] = zscore
                            except Exception as e:
                                traceback.print_exc()
                                logger.error(f"An error occurred in zscore for {operator} {metric}: {e}")

    def get_mva(self, date_list, module="csm"):
        if not date_list:
            return None  # Return if the date list is empty
        
        # Ensure dates are sorted for consistent key naming
        date_list = sorted(date_list)
        date_range_key = f"{date_list[0]}_{date_list[-1]}"
        
        aggregated_stats = {}
        count = len(date_list)
        
        data = {}
        if module == "csm":
            data = self.node_data
        elif module == "curated":
            data = self.curated_module_data
        elif module == "sdvt":
            data = self.sdvt_data

        # Initialize sums for all metrics
        
        for date in date_list:
            if date in data:
                for operator, metrics in data[date].items():
                    if operator not in aggregated_stats:
                        aggregated_stats[operator] = {}
                    for metric, values in metrics.items():
                        if metric not in aggregated_stats[operator]:
                            aggregated_stats[operator][metric] = {}
                        for variable, item in values.items():
                            if variable not in aggregated_stats[operator][metric]:
                                aggregated_stats[operator][metric][variable] = []
                            
                            aggregated_stats[operator][metric][variable].append(item)
                            
        data[date_range_key] = {}
        for operator, metrics in aggregated_stats.items():
            if operator not in data[date_range_key]:
                data[date_range_key][operator]  = {}
            for metric, values in metrics.items():
                if metric not in data[date_range_key][operator]:
                    data[date_range_key][operator][metric] = {}
                for variable, item_list in values.items():
                    if metric == "startTimestamp":
                        data[date_range_key][operator][metric][variable]  = date_list[0]
                    elif metric == "endTimestamp":
                        data[date_range_key][operator][metric][variable] = date_list[-1]
                    elif metric == 'totalUniqueAttestations':
                        valid_attest = [float(v) for v in metrics['totalUniqueAttestations']['metric'] if v is not None]
                        sum_attest = np.sum(valid_attest)
                        data[date_range_key][operator][metric][variable] = sum_attest
                    else:
                        if variable == 'metric' and metric in ATTEST_METRICS:
                            valid_values = [float(v) for v in metrics[metric][variable] if v is not None]
                            sum_values = np.sum(valid_values)
                            data[date_range_key][operator][metric]['sum'] = sum_values
                        if variable == 'attest_pct':
                            valid_metrics = [v for v in metrics[metric]['metric'] if v is not None]
                            sum_metric = np.sum(valid_metrics)
                            valid_attest = [v for v in metrics['totalUniqueAttestations']['metric'] if v is not None]
                            sum_attest = np.sum(valid_attest)
                            if valid_metrics and valid_attest: pct = self.calc_percent(sum_metric, sum_attest)
                            else: pct =  None
                            data[date_range_key][operator][metric][variable] = pct
                        else:
                            valid_values = [v for v in item_list if v is not None]
                            if valid_values:
                                mean = np.mean(valid_values)
                            else:
                                mean = None  # Set mean to None if no valid values exist
                            data[date_range_key][operator][metric][variable] = mean

    def calc_percent(self, stat, total_attest):
        if total_attest == 0:
            return float('nan')
        return (stat / total_attest) * 100 

    def calc_zscore(self, value, mean, std_dev):
        zscore = None
        if std_dev is not None and mean is not None:
            if std_dev == 0.0:
                # All values are identical; z-score is 0
                zscore = 0.0
            else:
                zscore = (value - mean) / std_dev
            
        return zscore