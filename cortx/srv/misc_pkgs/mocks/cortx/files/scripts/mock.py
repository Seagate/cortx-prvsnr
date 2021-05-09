#!/usr/bin/env python3

import sys
import logging

FORMAT = '%(asctime)s-%(message)s'
LOGGING_FILE = '/tmp/mock.log'


def main():
    """
    Main Mock logic

    Returns
    -------
    None

    """
    # pass all parameters "as is"
    logger.info(f"MOCK: {' '.join(sys.argv[1:])}")


if __name__ == '__main__':
    logging.basicConfig(format=FORMAT, filename=LOGGING_FILE)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    main()
