#!/usr/bin/env python

import sys
import logging

FORMAT = '%(asctime)s-%(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger(__name__)


def main():
    """
    Main Mock logic

    Returns
    -------
    None

    """
    logger.info(f"{sys.argv[1:]}")  # pass all parameters "as is"


if __name__ == '__main__':
    main()
