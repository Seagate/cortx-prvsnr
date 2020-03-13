import sys

from .salt import auth_init as _auth_init, StateFunExecuter
from ._api_cli import api_args_to_cli
from .api_spec import api_spec
from .commands import commands


# TODO
# - cache of pillar files
# - logic of cache update (watchers ?)
# - async API
# - typing
#
# - rollback
# - action might require a set of preliminary steps - hard
#   to describe using generic spec (yaml)


def auth_init(username, password, eauth='pam'):
    return _auth_init(username, password, eauth=eauth)


def run(command: str, *args, **kwargs):
    # do not expect ad-hoc credentials here
    kwargs.pop('password', None)
    kwargs.pop('username', None)
    kwargs.pop('eauth', None)

    if kwargs.pop('async', False):
        kwargs['loglevel'] = 'INFO'
        kwargs['logstream'] = 'stderr'
        kwargs['output'] = 'json'
        cli_args = api_args_to_cli(command, *args, **kwargs)
        cmd = ' '.join(['provisioner'] + cli_args)

        return StateFunExecuter.execute(
            'cmd.run', cmd
        )
    else:
        cmd = commands[command]
        return cmd.run(*args, **kwargs)


def _api_wrapper(fun):
    def f(*args, **kwargs):
        return run(fun, *args, **kwargs)
    return f


mod = sys.modules[__name__]
for fun in api_spec:
    setattr(mod, fun, _api_wrapper(fun))
