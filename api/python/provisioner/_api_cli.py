import sys
import subprocess
import logging

from provisioner import errors
from provisioner import serialize

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


# TODO tests
def api_args_to_cli(fun, *args, **kwargs):
    res = [fun]
    for k, v in kwargs.items():
        k = '--{}'.format(k.replace('_', '-'))
        if type(v) is not bool:
            res.extend([k, str(v)])
        elif v:
            res.extend([k])

    res.extend([str(a) for a in args])
    logger.debug("Cli command args: {}".format(res))

    return res


# TODO tests
def process_cli_result(
    stdout: str = None, stderr: str = None
):
    try:
        res = serialize.loads(stdout) if stdout else {}
    except errors.PrvsnrTypeDecodeError:
        logger.exception('Failed to decode provisioner output')
        res = serialize.loads(stdout, strict=False)

    if type(res) is not dict:
        raise errors.ProvisionerError(
            'Unexpected result {}'.format(stdout)
        )

    if 'exc' in res:
        raise res['exc']
    else:
        try:
            return res['ret']
        except KeyError:
            raise errors.ProvisionerError(
                "No return data found in '{}', stderr: '{}'"
                .format(stdout, stderr)
            )


def _run_cmd(cmd, **kwargs):
    try:
        res = subprocess.run(cmd, **kwargs)
    # subprocess.run fails expectedly
    except subprocess.CalledProcessError as exc:
        return process_cli_result(exc.stdout, exc.stderr)
    # subprocess.run fails unexpectedly
    except Exception as exc:
        raise errors.ProvisionerError(repr(exc)) from exc
    else:
        return process_cli_result(res.stdout, res.stderr)


# TODO test args preparation
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

    cli_args = api_args_to_cli(fun, *args, **kwargs)
    cmd = ['provisioner'] + cli_args

    return _run_cmd(
        cmd,
        input=_input,
        check=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


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
    'eos_update', 'fw_update', 'get_result'
]:
    setattr(mod, fun, _api_wrapper(fun))
