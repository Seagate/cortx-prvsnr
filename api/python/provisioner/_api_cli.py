import sys
import subprocess
import json
import logging

from provisioner.errors import ProvisionerError

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


def _api_call(fun, *args, **kwargs):
    # do not expect ad-hoc credentials here
    kwargs.pop('password', None)
    kwargs.pop('username', None)
    kwargs.pop('eauth', None)

    _input = None
    if _username and _password:
        _input = _password
        kwargs['username'] = _username
        kwargs['password'] = '-'
        kwargs['eauth'] = _eauth

    kwargs['loglevel'] = 'INFO'
    kwargs['logstream'] = 'stderr'
    kwargs['output'] = 'json'

    cmd = ['provisioner', fun]
    for k, v in kwargs.items():
        cmd.extend(['--{}'.format(k), str(v)])
    cmd.extend([str(a) for a in args])
    logger.debug("Command: {}".format(cmd))

    try:
        res = subprocess.run(
            cmd,
            input=_input,
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as exc:
        raise ProvisionerError(exc.stderr) from exc
    except Exception as exc:
        raise ProvisionerError(repr(exc)) from exc
    else:
        return json.loads(res.stdout) if res.stdout else None


def _api_wrapper(fun):
    def f(*args, **kwargs):
        return _api_call(fun, *args, **kwargs)
    return f


def auth_init(username, password, eauth='pam'):
    global _eauth
    global _username
    global _password
    _eauth = eauth
    _username = username
    _password = password


# TODO automate commands list discovering
mod = sys.modules[__name__]
for fun in [
    'pillar_get', 'get_params', 'set_params',
    'set_ntp', 'set_network', 'set_eosupdate_repo',
    'eos_update'
]:
    setattr(mod, fun, _api_wrapper(fun))
