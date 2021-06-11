#!/usr/bin/env python3

import sys
import os
import logging

FORMAT = '%(asctime)s-%(message)s'
LOGGING_FILE = '/tmp/mock.log'

mock_env = (
    'PRVSNR_MINI_FLOW',
    'PRVSNR_MINI_LEVEL',
    'PRVSNR_MINI_HOOK',
    'CORTX_VERSION',
    'CORTX_UPGRADE_VERSION'
)


def main():
    """
    Main Mock logic

    Returns
    -------
    None

    """
    # pass all parameters "as is"
    env = [f"{k}={os.environ[k]}" for k in mock_env if k in os.environ]
    logger.info(f"MOCK: {' '.join(sys.argv[1:])} {','.join(env)}")


if __name__ == '__main__':
    logging.basicConfig(format=FORMAT, filename=LOGGING_FILE)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    main()
