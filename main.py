# Main entry point for the application

import logging
import logging.config
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / 'src'))
from config import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)

from bot import run

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logger.info("Starting En Passant Bot...")
    run()
