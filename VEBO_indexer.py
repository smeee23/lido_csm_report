from JobRunner import JobRunner
import argparse
from dotenv import load_dotenv
import os
from logger_config import logger

load_dotenv()  # take environment variables from .env.

class ProcessEvents:
    def __init__(self, call_freq, rated_api_call):
        self.call_freq = call_freq
        self.rated_api_call = rated_api_call

    def run_job(self):
        job_runner = JobRunner(self.call_freq, self.rated_api_call)
        job_runner.run()

if __name__ == "__main__":
    logger.info("starting lido csm bot")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--call-freq', action='store', type=int, default=7600,
                        help='how often run loop is called, default is 2 hr')
    parser.add_argument('--rated-api-call', action='store_true',
                        help='use this flag to enable rated API call logic')
    args = parser.parse_args()

    ProcessEvents(args.call_freq, args.rated_api_call).run_job()