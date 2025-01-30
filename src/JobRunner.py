import traceback
from RatedHandler import RatedHandler
from S3ReadWrite import S3ReadWrite
from GaitKeeper import GaitKeeper
from VisualHandler import VisualHandler
from DataHandler import DataHandler
from ReportHandler import ReportHandler
from visualizations import plot_line, plot_histogram
import time
import base64
import json
import os
import time
from logger_config import logger
from utils import find_date_groups

class JobRunner:
    def __init__(self, operator_ids, rated_api_call):
        self.counter = 0
        self.operator_ids = operator_ids
        self.rated_api_call = rated_api_call
        sk = decrypt_string(os.getenv("AWS_S3_SECRET_KEY"), os.getenv("KEY"))
        self.s3ReadWriter = S3ReadWrite(sk, os.getenv("AWS_S3_ACCESS_KEY"))
        self.DataHandler =  DataHandler()
        self.VisualHandler = VisualHandler(self.operator_ids, self.DataHandler)
        self.ReportHandler = ReportHandler(self.operator_ids, self.DataHandler)

    def run(self):
        try:
            if self.rated_api_call:
                logger.info("checking Rated.network stats [--rated-api-call set to True]")
                rated_handler = RatedHandler(os.getenv("RATED_API_SK_4"))
                rated_handler.write_api_data(s3=self.s3ReadWriter)

            if self.operator_ids:
                self.DataHandler.load_data(s3=self.s3ReadWriter)

                nos = self.DataHandler.node_data
                agg_data = self.DataHandler.agg_data
  
                self.DataHandler.get_mva(['2025-01-16', '2025-01-15', '2025-01-14', '2025-01-13', '2025-01-12'], module="csm")
                self.DataHandler.get_mva(['2025-01-16', '2025-01-15', '2025-01-14', '2025-01-13', '2025-01-12'], module="sdvt")
                self.DataHandler.get_mva(['2025-01-16', '2025-01-15', '2025-01-14', '2025-01-13', '2025-01-12'], module="curated")
                
                self.DataHandler.get_statistics(module="csm")
                self.DataHandler.get_zscores(module="csm")

                self.DataHandler.get_statistics(module="sdvt")
                self.DataHandler.get_zscores(module="sdvt")

                self.DataHandler.get_statistics(module="curated")
                self.DataHandler.get_zscores(module="curated")

                for date, operators in self.DataHandler.node_data.items():
                    for id, stats in operators.items():
                        if "107" in id:
                            print(date)
                            print(id)
                            for metric, values in stats.items():
                                if metric == "sumWrongHeadVotes":
                                    print(metric, values)

                self.VisualHandler.generate_histograms(node_data=nos, date="2025-01-12_2025-01-16", sdvt_data=self.DataHandler.sdvt_data, curated_module_data=self.DataHandler.curated_module_data)
                self.VisualHandler.generate_time_series(data=nos, agg_data=agg_data)

                self.ReportHandler.generate_report()

            last_write = int(time.time())
            self.s3ReadWriter.write_data("lido_csm/last_write", last_write)
            logger.info(f"round {self.counter}")
            self.s3ReadWriter.write_logs()
            self.counter += 1
        
        except Exception as e:
            traceback.print_exc()
            logger.error(f"An error occurred in build_from_creation: {e}")

    def check_s3(self, key, value, tag):
        result = self.s3ReadWriter.get_data(key, tag)
        if result == "no_key":
            self.s3ReadWriter.write_data(key, value, tag)
            logger.info(f"New object {key}{tag}")
        elif result:
            if(result != value):
                self.s3ReadWriter.write_data(key, value, tag)
                logger.info(f"Overwrite object {key}{tag}")

    def refactor_pool(self, pool_dict):
        pool_dict["acceptedTokenInfo"] = [{**pool_dict["acceptedTokenInfo"][key], 'address': key} for key in pool_dict["acceptedTokens"]]
        pool_dict.pop("acceptedTokens")
        return pool_dict

def decrypt_string(encrypted_base64, encryption_key):
    encrypted = base64.b64decode(encrypted_base64).decode('latin1')

    decrypted = ''

    for i in range(len(encrypted)):
        char_code = ord(encrypted[i]) ^ ord(encryption_key[i % len(encryption_key)])
        decrypted += chr(char_code)

    return decrypted