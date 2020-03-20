import sys
import logging

from .salt import auth_init as _auth_init
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

logger = logging.getLogger(__name__)


def auth_init(username, password, eauth='pam'):
    return _auth_init(username, password, eauth=eauth)


def run(command: str, *args, **kwargs):
    cmd = commands[command]
    logger.debug("Executing command {}".format(cmd))
    return cmd.run(*args, **kwargs)


def _api_wrapper(fun):
    def f(*args, **kwargs):
        return run(fun, *args, **kwargs)
    return f


mod = sys.modules[__name__]
for fun in api_spec:
    setattr(mod, fun, _api_wrapper(fun))
