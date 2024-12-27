import boto3
import json
from logger_config import logger

class S3ReadWrite:
    def __init__(self, aws_secret_access_key, aws_access_key_id):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key, 
            region_name="us-east-1"
        )
        self.bucket_name = 'justcausepools'
    
    def get_data(self, file_key, tag=""):
        try: 
            # Fetch the file from S3
            response = self.s3.get_object(Bucket=self.bucket_name, Key=file_key+tag)

            # Read the content of the file
            file_content = response['Body'].read().decode('utf-8')

            # Parse the JSON content
            data = json.loads(file_content)

            # Now, 'data' is a Python dictionary containing the data from the JSON file
            return data
        
        except self.s3.exceptions.NoSuchKey:  # Handle specific exception for missing file
            logger.info(f"File '{file_key+tag}' does not exist in the bucket.")
            return None
    
        except Exception as e: 
            logger.error(f"An error occurred: {e}")
            return None
        
    def write_data(self, file_key, data, tag=""):
        try:
            # Use the put_object method
            json_data = json.dumps(data)
            self.s3.put_object(
                Body=json_data,
                Bucket=self.bucket_name,
                Key=file_key+tag,
                CacheControl='max-age=600'
            )
            logger.info(f"Successfully uploaded {file_key+tag} to {self.bucket_name}.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
    
    def write_logs(self):
        try:
            self.s3.upload_file(
                Filename='./app.log',
                Bucket=self.bucket_name,
                Key='lido_csm/app.log',
            )
            logger.info(f"Successfully uploaded app.log to {self.bucket_name}.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")




