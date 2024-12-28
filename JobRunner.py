import traceback
from RatedHandler import RatedHandler
from S3ReadWrite import S3ReadWrite
from GaitKeeper import GaitKeeper
from DataHandler import DataHandler
from visualizations import plot_scatter, plot_line
import time
import base64
import json
import os
import time
from logger_config import logger

class JobRunner:
    def __init__(self, freq_call, rated_api_call):
        self.counter = 0
        self.freq_call = freq_call
        self.rated_api_call = rated_api_call
        sk = decrypt_string(os.getenv("AWS_S3_SECRET_KEY"), os.getenv("KEY"))
        self.s3ReadWriter = S3ReadWrite(sk, os.getenv("AWS_S3_ACCESS_KEY"))
        self.DataHandler =  DataHandler()

    def run(self):
        while(True):
            try:
                if self.rated_api_call:
                    logger.info("checking Rated.network stats [--rated-api-call set to True]")
                    rated_handler = RatedHandler(os.getenv("RATED_API_SK"))
                    rated_handler.write_api_data(s3=self.s3ReadWriter)

                files = self.s3ReadWriter.get_dir_files("lido_csm/operator_data/")
                self.DataHandler.load_data(files=files, s3=self.s3ReadWriter)
                nos = self.DataHandler.node_data
                for k, v in nos.items():
                    for id, val in v.items():
                        print(id)
                        print(val)
                
                self.DataHandler.calculate_statistics()
                temp = self.DataHandler.node_stats
                for k, date in temp.items():
                    for metric, val in date.items():
                        print(metric, val)
                        print(nos[k]["CSM Operator 37 - Lido Community Staking Module"][metric])

                plot_scatter(data=nos, variable="avgValidatorEffectiveness", operator_ids=[37, 135], date="2024-12-27", title="Title")
                plot_scatter(data=nos, variable="avgInclusionDelay", operator_ids=[37, 135], date="2024-12-27", title="Title")
                plot_scatter(data=nos, variable="avgProposerEffectiveness", operator_ids=[37, 135], date="2024-12-27", title="Title")
                #plot_line(nos, "avgValidatorEffectiveness", [37, 135])
                last_write = int(time.time())
                self.s3ReadWriter.write_data("lido_csm/last_write", last_write)
                logger.info(f"round {self.counter}")
                self.s3ReadWriter.write_logs()
                self.counter += 1
            
            except Exception as e:
                traceback.print_exc()
                logger.error(f"An error occurred in build_from_creation: {e}")

            time.sleep(self.freq_call) #sleep 2 hr

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