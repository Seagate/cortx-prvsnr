import sys
import subprocess
import json
import logging

from provisioner import errors

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


def _run_cmd(cmd, **kwargs):
    try:
        logger.debug("Executing command {}".format(cmd))
        res = subprocess.run(cmd, **kwargs)
    # subprocess.run fails expectedly
    except subprocess.CalledProcessError as exc:
        res = json.loads(exc.stdout) if exc.stdout else {}
        cli_exc = res.get('exc', {})
        cli_exc_type, cli_exc_args = cli_exc.get('type'), cli_exc.get('args')

        if cli_exc_args and cli_exc_type:
            prvsnr_error_type = getattr(errors, cli_exc_type, None)
            # cli fails expectedly
            if prvsnr_error_type:
                _exc = prvsnr_error_type(*cli_exc_args)
            # cli fails unexpectedly - unexpected error
            else:
                _exc = errors.ProvisionerError(cli_exc_type, *cli_exc_args)
        else:
            # cli fails unexpectedly - unexpected output
            _exc = errors.ProvisionerError(exc.stderr)
        logger.exception("Failed to execute command")
        raise _exc from exc
    # subprocess.run fails unexpectedly
    except Exception as exc:
        logger.exception("Failed to execute command")
        raise errors.ProvisionerError(repr(exc)) from exc
    else:
        _res = json.loads(res.stdout) if res.stdout else {}
        try:
            return _res['ret']
        except KeyError:
            logger.error(
                "No return data found ib {}".format(res.stdout)
            )
            raise errors.ProvisionerError(
                'No return data found in {}'.format(res.stdout)
            )


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

    cmd = ['provisioner', fun]
    for k, v in kwargs.items():
        k = '--{}'.format(k.replace('_', '-'))
        if type(v) is not bool:
            cmd.extend([k, str(v)])
        elif v:
            cmd.extend([k])

    cmd.extend([str(a) for a in args])
    
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
    'eos_update'
]:
    setattr(mod, fun, _api_wrapper(fun))