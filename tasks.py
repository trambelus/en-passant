from invoke import task
import sys
from pathlib import Path
import subprocess
import logging

PROTOC_COMMAND = f'protoc --proto_path={Path("src/message/proto").resolve()} --python_out={Path("src/message").resolve()} ' # Append the file names to this string

logger = logging.getLogger(__name__)

@task
def compile_proto(ctx):
    '''Compile the protocol buffer files.'''
    logger.info('Compiling protocol buffer files...')
    # Get all the .proto files in the src/message/proto directory
    proto_files = Path.glob(Path('src/message/proto').resolve(), '*.proto')
    # Compile each file
    for proto_file in proto_files:
        logger.debug('Compiling %s', proto_file)
        result = subprocess.run(PROTOC_COMMAND + str(proto_file))
        if result.returncode != 0:
            logger.error('Failed to compile protocol buffer file %s', proto_file)
            logger.error('Error code: %d', result.returncode)
            sys.exit(1)

    logger.info('Complete.')

@task(compile_proto)
def run_bot(ctx):
    '''Run the bot.'''
    logger.info('Running bot...')
    result = subprocess.run('python main.py', shell=True)
    # shell=True lets us use the environment variables, including the Python venv
    if result.returncode != 0:
        logger.error('Failed to run bot.')
        logger.error('Error code: %d', result.returncode)
        sys.exit(1)

    logger.info('Complete.')

@task(compile_proto)
def run_engine(ctx):
    '''Run the engine.'''
    logger.info('Running engine...')
    result = subprocess.run('python src/engine/engine.py')
    if result.returncode != 0:
        logger.error('Failed to run engine.')
        logger.error('Error code: %d', result.returncode)
        sys.exit(1)
    logger.info('Complete.')
