import yaml

from .errors import BadPillarDataError


# TODO test
def load_yaml_str(data):
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise BadPillarDataError(str(exc))


# TODO test
def dump_yaml_str(data, width=1, indent=4):
    return yaml.dump(
        data,
        default_flow_style=False,
        canonical=False,
        width=width,
        indent=indent
    )


# TODO test
# TODO streamed read
def load_yaml(path):
    try:
        return load_yaml_str(path.read_text())
    except yaml.YAMLError as exc:
        raise BadPillarDataError(str(exc))


# TODO test
# TODO streamed write
def dump_yaml(path, data):
    path.write_text(dump_yaml_str(data))
