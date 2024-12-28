from logger_config import logger
from GaitKeeper import GaitKeeper
import traceback
import time

class DataHandler:
    def __init__(self):
        self.agg_data = {}  

    def load_data(self, files, s3):
        for key in files:
            try:
                op_data = self.normalize_data(s3.get_data(key))
                id = key.split('/')[2]
                
                if id not in self.agg_data:
                    self.agg_data[id] = op_data
                else:
                    for date in op_data:
                        self.agg_data[id][date] = op_data[date]

            except Exception as e:
                traceback.print_exc()
                logger.error(f"An error occurred in Rated.network API check: {e}")
                time.sleep(1)
    
    def normalize_data(self, data):
        normalized_data = data

        for date, values in data.items():
            num_vals = values["validatorCount"]
            for k, v in values.items():
                if "sum" in k and v is not None:
                    print(k)
                    print(v, num_vals)
                    print(f"avg{k[2:]}")
                    print(v / num_vals)
                    #normalized_data[f"avg{k[2:]}"]
        return normalized_data
