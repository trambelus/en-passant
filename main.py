# Main entry point for the application

import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / 'src'))


from bot import run

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logger.info("Starting En Passant Bot...")
    run()