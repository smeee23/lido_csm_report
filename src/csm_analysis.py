from JobRunner import JobRunner
import argparse
from dotenv import load_dotenv
import os
from logger_config import logger

load_dotenv()  # take environment variables from .env.

class ProcessEvents:
    def __init__(self, operator_ids, rated_api_call):
        if operator_ids:
            self.operator_ids = [int(x) for x in operator_ids.split(",")]
        else: self.operator_ids = None
        self.rated_api_call = rated_api_call

    def run_job(self):
        job_runner = JobRunner(self.operator_ids, self.rated_api_call)
        job_runner.run()

if __name__ == "__main__":
    logger.info("starting lido csm bot")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--operator-ids', action='store', type=str, default="",
                        help='how often run loop is called, default is 2 hr')
    parser.add_argument('--rated-api-call', action='store_true',
                        help='use this flag to enable rated API call logic')
    args = parser.parse_args()

    ProcessEvents(args.operator_ids, args.rated_api_call).run_job()