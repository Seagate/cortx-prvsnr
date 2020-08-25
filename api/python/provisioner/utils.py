import yaml
import logging
import time
from typing import Tuple, Union
from pathlib import Path
import subprocess
from .errors import (
    BadPillarDataError, ProvisionerError
)

logger = logging.getLogger(__name__)


# TODO test
def load_yaml_str(data):
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError as exc:
        logger.exception("Failed to load pillar data")
        raise BadPillarDataError(str(exc))


# TODO test
def dump_yaml_str(
    data,
    width=1,
    indent=4,
    default_flow_style=False,
    canonical=False,
    **kwargs
):
    return yaml.safe_dump(
        data,
        default_flow_style=default_flow_style,
        canonical=canonical,
        width=width,
        indent=indent,
        **kwargs
    )


# TODO test
# TODO streamed read
def load_yaml(path):
    path = Path(str(path))
    try:
        return load_yaml_str(path.read_text())
    except yaml.YAMLError as exc:
        logger.exception("Failed to load pillar data")
        raise BadPillarDataError(str(exc))


# TODO test
# TODO streamed write
def dump_yaml(path, data, **kwargs):
    path = Path(str(path))
    path.write_text(dump_yaml_str(data, **kwargs))


# TODO IMPROVE:
#   - exceptions in check callback
def ensure(
    check_cb, tries=10, wait=1, name=None,
    expected_exc: Union[Tuple, Exception, None] = None
):
    if name is None:
        try:
            name = check_cb.__name__
        except AttributeError:
            name = str(check_cb)

    ntry = 0
    while True:
        exc = None
        ntry += 1
        logger.debug(
            'Try #{}/{} for {}'
            .format(ntry, tries, name)
        )

        try:
            if check_cb():
                return
        except Exception as _exc:
            if expected_exc and isinstance(_exc, expected_exc):
                logger.info(
                    'Try #{}/{} for {} failed: {!r}'
                    .format(ntry, tries, name, _exc)
                )
                exc = _exc
            else:
                raise

        if ntry < tries:
            time.sleep(wait)
        else:
            if exc:
                raise exc
            else:
                raise ProvisionerError('no more tries')
