#! /usr/bin/python3

import logging
import socket
import time
import sys

LOG_DIR = "/var/log/demoLogger/"
HOSTNAME = socket.gethostname()
LOG_FILE = LOG_DIR + HOSTNAME + ".log"

def initialize_logger():
    log = logging.getLogger("demo-logger")
    log.setLevel(level=logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(level=logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log
    
def infi_logger(logger=None):
    i = 0
    while True:
        logline = f"Logging count {i}"
        if logger:
            logger.info(logline)
        else:
            print(logline)
        time.sleep(20)
        i += 1


if __name__ == "__main__":
    try:
        logger = initialize_logger()
        infi_logger(logger)
    except KeyboardInterrupt:
        print("Stopping the demoLogger.")
        sys.exit(0)
    except Exception as err:
        print(err)
        sys.exit(1)

