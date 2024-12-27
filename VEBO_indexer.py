from JobRunner import JobRunner
import argparse
from dotenv import load_dotenv
import os
from logger_config import logger

load_dotenv()  # take environment variables from .env.

class ProcessEvents:
    def __init__(self, call_freq):
        self.call_freq = call_freq * 60

    def run_job(self):
        job_runner = JobRunner(self.call_freq)
        job_runner.run()
        

if __name__ == "__main__":
    logger.info("Starting lido csm bot")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--call-freq', action='store', type=int, default=1,
                        help='how often api is called, default is 1 min')
    args = parser.parse_args()
    ProcessEvents(args.call_freq).run_job()