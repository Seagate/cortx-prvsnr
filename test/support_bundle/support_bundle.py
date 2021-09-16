#! /usr/bin/python3

import tarfile
import os
import sys

from sb_config import ARCHIEVE_DIR, SB_FILE_PATH

class SupportBundleError(Exception):

    """Generic Exception with error code and output."""

    def __init__(self, rc, message, *args):
        """Initialize with custom error message and return code."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Format error string."""
        if self._rc == 0: return self._desc
        return "SupportBundleError(%d): %s" %(self._rc, self._desc)

class SupportBundle(object):

    def generate_tar(self):
        try:
            with tarfile.open(SB_FILE_PATH, "w:gz") as tar_handle:
                for root, _, files in os.walk(ARCHIEVE_DIR):
                    for file in files:
                        tar_handle.add(os.path.join(root, file))
        except Exception as err:
            raise SupportBundleError(1, str(err))

if __name__ == "__main__":
    try:
        SupportBundleObj = SupportBundle()
        SupportBundleObj.generate_tar()
    except KeyboardInterrupt:
        print("Failed to generate support bundle.")
        sys.exit(0)
    except Exception as err:
        print(err)
        sys.exit(1)

