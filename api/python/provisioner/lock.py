#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#
import json
import os
from pathlib import Path
from string import Template
from typing import Iterable, Callable

from .config import PRVSNR_LOCKS_FILES_DIR, LockMetaDataFields
from .errors import LockFileError
from .salt import local_minion_id, function_run
from .salt_minion import check_salt_minions_are_ready
from .vendor import attr
from . import utils


@attr.s(auto_attribs=True)
class Lock:
    """Base locking class that provides API for blocking concurrent
    provisioner API calls.
    """

    targets: str = attr.ib(
        default="all"
    )
    _lockfile: str = attr.ib(
        init=False,
        default=None
    )
    _lock_filename_tmpl = Template("provisioner.$TARGETS.lock")

    @staticmethod
    def _check_pid(pid: str, target: str) -> bool:
        """Check if process is running by given pid and on given salt target.

        Parameters
        ----------
        pid: str
            process pid for check
        target: str
            target where need to verify the pid of a process

        Returns
        -------
        bool:
            True if process by given `pid` is alive on `target`.
            False otherwise

        """
        # run the command: `salt $target ps.kill_pid $pid signal=0`
        # NOTE: we send 0 signal to check for the existence of a process ID
        res = function_run('ps.kill_pid', fun_args=[pid],
                           fun_kwargs=dict(signal=0),
                           targets=target)
        return bool(res[target])

    def _get_lock_files(self) -> Iterable[Path]:
        """
        Get the provisioner lock files

        Returns
        -------
        iter:
            Iterator object over all provisioner lock files in the lock dir
        """
        # NOTE: search for files by pattern 'provisioner.*.lock'
        return Path(PRVSNR_LOCKS_FILES_DIR).glob(
            self._lock_filename_tmpl.substitute(TARGETS="*"))

    def _handle_old_lock_files(self):
        """
        Method handles all existing provisioner lock files:

        1. Checks if they have the correct metadata and delete if don't
        2. If lock file metadata is not actual, delete it

        Returns
        -------
        None

        """
        for lock_file in self._get_lock_files():
            try:
                lock_metadata = utils.load_json(lock_file)
            except json.decoder.JSONDecodeError:
                # Metadata is not well-formatted as proper json
                pass  # delete this lock file in the end of the loop
            else:
                if lock_metadata:
                    target = lock_metadata.get(
                        LockMetaDataFields.SOURCE_TARGET.value, None)
                    pid = lock_metadata.get(
                        LockMetaDataFields.PID, None)
                    if (target and pid and
                            check_salt_minions_are_ready(targets=[target]) and
                            self._check_pid(pid, target)):
                        raise LockFileError(f"Process with PID='{pid}' is "
                                            f"running on target='{target}'")

            # NOTE: Delete file in the following cases:
            #  1. Necessary metadata fields are missed
            #  2. The lock file initiator target is not alive
            #  3. The process by given pid is not running
            lock_file.unlink()

    def acquire(self):
        """
        Acquire the lock. It tries to create the lock file.

        Returns
        -------

        """
        self._handle_old_lock_files()

        lock_filename = self._lock_filename_tmpl.substitute(
            TARGETS=str(self.targets))
        self._lockfile = PRVSNR_LOCKS_FILES_DIR / lock_filename

        data = {
            LockMetaDataFields.PID.value: os.getpid(),
            LockMetaDataFields.SOURCE_TARGET.value: local_minion_id()
        }

        with open(self._lockfile, "w") as fh:
            json.dump(data, fh)

    def release(self):
        """
        Release the lock. It releases the lock file.

        Returns
        -------
        None

        """
        if self._lockfile and Path(self._lockfile).exists():
            Path(self._lockfile).unlink()

    def __enter__(self):
        """

        Returns
        -------

        """
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        Parameters
        ----------
        exc_type:
            Exception type
        exc_val:
            Exception value
        exc_tb:
            Exception traceback

        Returns
        -------

        """
        self.release()


def api_lock(fun) -> Callable:
    """
    Decorator to prevent concurrent provisioner API calls

    Parameters
    ----------
    fun

    Returns
    -------
    Callable:
        the new wrapped function which supports the provisioner lock

    """

    def wrapper(*args, **kwargs):
        with Lock():
            return fun(*args, **kwargs)

    return wrapper
