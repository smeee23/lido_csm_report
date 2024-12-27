import requests
from datetime import datetime, timedelta, timezone
from logger_config import logger
from GaitKeeper import GaitKeeper
import traceback

class RatedHandler:
    def __init__(self, sk):
        self.sk = sk
        self.node_operator_ids = [37, 135]
        self.rated_ids = ["Lido", "Lido Community Staking Module"]
        #self.no_index = [2, 5, 10, 37, 39, 66, 80, 91, 102, 103]
        for n in range(0, 235):
            self.rated_ids.append(f"CSM Operator {n} - Lido Community Staking Module")

    def check_effectiveness(self, rated_data):
        try:
            for id in self.rated_ids:
                if id == "Lido": entity_type = "pool"
                else: entity_type = "poolShare"
                urls = {
                    "attest": f"https://api.rated.network/v1/eth/entities/{id}/attestations",
                    "effective": f"https://api.rated.network/v1/eth/entities/{id}/effectiveness",
                }
                yest, today = self.get_last_days(days=5)
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
                        "Authorization": f"Bearer {self.sk}",  # Use the appropriate header key for your API
                        "Content-Type": "application/json",
                    }

                    # Make the GET request
                    response = requests.get(base_url, headers=headers, params=params)

                    # Handle the response
                    if response.status_code == 200:
                        data = response.json()
                        #msg = self.format_json(data)
                        logger.info("Response Data:", data)
                        print(f"\n\n{key}\n\n")
                        print(data)
                        #return self.format_json(msg)
                        results.append(data)
                    else:
                        logger.error(f"Request failed with status code {response.status_code}: {response.text}")
                        print(f"Request failed with status code {response.status_code}: {response.text}")
                        
                #print(results)
                combined_data = self.combine_jsons(results)
                if id not in rated_data:
                    rated_data[id] = combined_data
                else:
                    for timestamp, values in combined_data.items():
                        rated_data[id][timestamp] = values
            print(rated_data) 
            return rated_data   
        except Exception as e:
                traceback.print_exc()
                logger.error(f"An error occurred in Rated.network API check: {e}")
                return None

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
