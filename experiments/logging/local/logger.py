#! /usr/bin/python3

import logging
import socket
import time
import os
import sys
import argparse

# LOG_DIR, LOG_LEVEL should be stored in Config since,
# CORTX services will read these values from the Config.
LOG_DIR = "/var/log/cortx/"
LOG_LEVEL = logging.DEBUG
HOSTNAME = socket.gethostname().replace('.', '-')

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
    desc = ("Logs the sample statements in the <log_dir>/"
            "<app_name>/<host_name>.log file.")
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-n', '--app-name', help="Logger App Name.")
    args = parser.parse_args()
    APP = args.app_name if args.app_name else "demo-logger"
    LOG_DIR = os.path.join(LOG_DIR, APP)
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, HOSTNAME + ".log")
    try:
        logger = initialize_logger()
        infi_logger(logger)
    except KeyboardInterrupt:
        print(f"Stopping the {APP} service.")
        sys.exit(0)
    except Exception as err:
        print(err)
        sys.exit(1)

