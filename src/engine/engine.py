# Waits to receive messages from the client component, and manages the engine sessions.

import logging

logger = logging.getLogger(__name__)

from .engine_session import EngineSession

def run():
    logger.info("Starting En Passant Engine...")
    pass # TODO: implement

if __name__ == '__main__':
    run()
