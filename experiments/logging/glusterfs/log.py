import logging
import time
import os
# create logger
logger = logging.getLogger({os.getenv('POD_NAME')})
logger.setLevel(logging.DEBUG)

# log path will come form confstore
log_path = f"/share/var/log/cortx/{os.getenv('POD_NAME')}"
if not os.path.exists(log_path):
    os.makedirs(log_path)

ch = logging.FileHandler(f"{log_path}/{os.getenv('POD_NAME')}.log")
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

while True:
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')
    time.sleep(5)
