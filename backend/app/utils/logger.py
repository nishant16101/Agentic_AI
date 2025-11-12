import logging 
from logging.handlers import RotatingFileHandler
from pathlib import Path

#configuration
LOG_DIR  = Path("logs")
LOG_FILE = LOG_DIR/"app.log"
MAX_BYTES = 5*1024*1024
BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

LOG_DIR.mkdir(exist_ok=True)

def get_logger(name:str = "agentic workspace")-> logging.Logger:
    """Returns a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)

        #file handler
        file_handler = RotatingFileHandler(
            LOG_FILE,maxBytes=MAX_BYTES,backupCount=BACKUP_COUNT,encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger


root_logger = get_logger()