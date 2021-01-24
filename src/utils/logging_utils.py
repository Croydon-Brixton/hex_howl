import os
import logging
import logging.handlers
import pathlib

LOG_DIR = pathlib.Path("/home/ec2-user/environment/logs")


def initialize_logger(logger, log_name=None):
    """
    Initialize the given `logger` to log to files in the given `log_name` directory.
    If log_name is None, then no logs are stored.
    """
    
    # Set up general logger and formatting
    logger.setLevel(logging.DEBUG)  # listen to everything
    formatter = logging.Formatter('%(asctime)s [%(name)-10s] [%(threadName)-12s] %(message)s [in %(pathname)s:%(lineno)d]')
    

    # If file_name provided, add file handler for logs
    if log_name:
        if not os.path.exists(LOG_DIR / f"{log_name}"):
            os.mkdir(LOG_DIR / f"{log_name}")
            
        file_handler = logging.handlers.RotatingFileHandler(LOG_DIR / f"{log_name}/{log_name}.log", maxBytes=1000240, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    
    # Add console handler for logs:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)