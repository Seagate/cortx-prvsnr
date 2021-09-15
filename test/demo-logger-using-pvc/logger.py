#! /usr/bin/python3

import logging
import socket
import time
import os
import sys

LOG_DIR = "/var/log/"
APP = "demo-logger"
HOSTNAME = socket.gethostname().replace('.', '-')
LOG_FILE = os.path.join(LOG_DIR, APP, HOSTNAME + ".log")
LOG_LEVEL = logging.DEBUG

def initialize_logger():
    log = logging.getLogger(APP)
    log.setLevel(level=LOG_LEVEL)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(level=LOG_LEVEL)
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
        time.sleep(5)
        i += 1


if __name__ == "__main__":
    try:
        logger = initialize_logger()
        infi_logger(logger)
    except KeyboardInterrupt:
        print(f"Stopping the {APP}.")
        sys.exit(0)
    except Exception as err:
        print(err)
        sys.exit(1)

