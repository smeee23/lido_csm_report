import traceback
from RatedHandler import RatedHandler
from S3ReadWrite import S3ReadWrite
from GaitKeeper import GaitKeeper
import time
import base64
import json
import os
import time
from logger_config import logger

class JobRunner:
    def __init__(self, freq_call):
        self.counter = 0
        self.freq_call = freq_call
        sk = decrypt_string(os.getenv("AWS_S3_SECRET_KEY"), os.getenv("KEY"))
        self.s3ReadWriter = S3ReadWrite(sk, os.getenv("AWS_S3_ACCESS_KEY")) 

    def run(self):
        while(True):
            try:
                logger.info(f"checking Rated.network stats")
                handler = RatedHandler(os.getenv("RATED_API_SK_ALT"))
                rated_data = handler.check_effectiveness(rated_data={})
                self.s3ReadWriter.write_data("lido_csm/rated_data", rated_data)

                last_write = int(time.time())
                self.s3ReadWriter.write_data("lido_csm/last_write", last_write)
                logger.info(f"round {self.counter}")
                self.s3ReadWriter.write_logs()
                self.counter += 1
            
            except Exception as e:
                #traceback.print_exc()
                logger.error(f"An error occurred in build_from_creation: {e}")

            time.sleep(7200) #sleep 2 hr
                        
    def format_key(self, key):
        return key[0:8] + "..." + key[-6:]

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