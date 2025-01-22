import requests
from datetime import datetime, timedelta, timezone
from logger_config import logger
from GaitKeeper import GaitKeeper
import traceback
import time
from utils import LIDO_CURATED, LIDO_SDVT

class RatedHandler:
    def __init__(self, sk):
        self.sk = sk
        self.node_operator_ids = [37, 135]
        self.rated_ids = []#["Lido", "Lido Community Staking Module"]
        #for n in range(0, 400):
        #    self.rated_ids.append(f"CSM Operator {n} - Lido Community Staking Module")
        for id in LIDO_CURATED:
            self.rated_ids.append(f"{id} - Lido")  
        for id in LIDO_SDVT:
            self.rated_ids.append(f"{id} - Lido SimpleDVT Module")  

    def write_api_data(self, s3):
        for id in self.rated_ids:
            if id == "Lido": entity_type = "pool"
            else: entity_type = "poolShare"

            existing_data = s3.get_data(f"lido_csm/operator_data/{id}")

            urls = {
                "attest": f"https://api.rated.network/v1/eth/entities/{id}/attestations",
                "effective": f"https://api.rated.network/v1/eth/entities/{id}/effectiveness",
                #"rewards": f"https://api.rated.network/v1/eth/entities/{id}/rewards",
                #"penalties": f"https://api.rated.network/v1/eth/entities/{id}/penalties",
            }

            #yest, today = self.get_last_days(days=4)
            yest, today = "2025-01-12", "2025-01-16"
            params = {
                "fromDate": yest,
                "entityType": entity_type,
                "toDate": today,
                "utc": "false",  # "false" for ETH chain days
            }
            
            results = []
            for key, base_url in urls.items():
                # Headers
                headers = {
                    "Authorization": f"Bearer {self.sk}",  
                    "Content-Type": "application/json",
                }

                # Make the GET request
                try:
                    response = requests.get(base_url, headers=headers, params=params)
                

                    # Handle the response
                    if response.status_code == 200:
                        data = response.json()
                        logger.info("Response Data:", data)
                        results.append(data)
                    else:
                        logger.error(f"Request failed with status code {response.status_code}: {response.text}")
                        print(f"Request failed with status code {response.status_code}: {response.text}")

                except Exception as e:
                    traceback.print_exc()
                    logger.error(f"An error occurred in Rated.network API check: {e}")
                    time.sleep(1)

            combined_data = self.combine_jsons(results)
            print(combined_data)
            existing_data = s3.get_data(f"lido_csm/operator_data/{id}")
            if existing_data:
                for date, stats in list(existing_data.items()):
                    if date not in combined_data:
                        combined_data[date] = {}
                    combined_data[date].update(stats)
       
            s3.write_data(f"lido_csm/operator_data/{id}", combined_data)

    def get_last_days(self, days=1):
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)
        return start_date.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
    
    def combine_jsons(self, json_data_list):
        combined_data = {}

        for json_data in json_data_list:
            for result in json_data.get('results', []):
                # Extract the key (endTimestamp)
                end_timestamp = result.get('endTimestamp')[:-9]
                if not end_timestamp:
                    continue
                
                # Remove unwanted keys
                filtered_result = {
                    key: value
                    for key, value in result.items()
                    if key not in {"hour", "startDay", "endDay", "startDate", "endDate", "date", "day"}
                }
                
                # Combine the filtered result under the endTimestamp key
                if end_timestamp not in combined_data:
                    combined_data[end_timestamp] = {}
                combined_data[end_timestamp].update(filtered_result)

        return combined_data
