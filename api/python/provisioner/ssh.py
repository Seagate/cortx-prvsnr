import logging
from pathlib import Path
from typing import Union

from .utils import run_subprocess_cmd

logger = logging.getLogger(__name__)


# TODO TEST EOS-8473
def keygen(
    priv_key_path: Union[Path, str],
    comment: str = '',
    passphrase: str = ''
):
    run_subprocess_cmd(
        (
            "ssh-keygen -t rsa -b 4096 -o -a 100".split() +
            ['-C', comment, '-N', passphrase, '-f', str(priv_key_path)]
        ),
        input='y'
    )


# TODO TEST EOS-8473
def copy_id(
    host: str,
    user: str = None,
    port: int = None,
    priv_key_path: Union[Path, str] = None,
    force=False,
    ssh_options=None,
):
    cmd = ['ssh-copy-id']

    if force:
        cmd.append('-f')

    if priv_key_path:
        cmd.extend(['-i', str(priv_key_path)])

    if port:
        cmd.extend(['-p', str(port)])

    if ssh_options is not None:
        for opt in ssh_options:
            cmd.extend(['-o', opt])

    cmd.append(f"{user}@{host}" if user else host)

    run_subprocess_cmd(cmd)
