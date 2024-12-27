import logging
from logging.handlers import RotatingFileHandler

# Define the logger name
logger = logging.getLogger('my_app')
logger.setLevel(logging.INFO)

# Set up the RotatingFileHandler
log_file = 'app.log'
rotating_handler = RotatingFileHandler(log_file, maxBytes=1e6, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)
logger.addHandler(rotating_handler)