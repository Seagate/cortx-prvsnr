__virtualname__ = 'provisioner'


try:
    import provisioner
except ImportError:
    import sys
    import subprocess
    from pathlib import Path
    # TODO pip3 installs provisioner to /usr/local/lib/python3.6/site-packages
    #      but that directory is not listed in salt's sys.path,
    #      EOS-5401 might be related
    try:
        prvsnr_pkg_path = subprocess.run(
            "python3 -c 'import provisioner; print(provisioner.__file__)'",
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True
        ).stdout.strip()
        sys.path.insert(0, str(Path(prvsnr_pkg_path).parent.parent))
        import provisioner
    except Exception:
        HAS_PROVISIONER = False
    else:
        HAS_PROVISIONER = True
else:
    HAS_PROVISIONER = True


if HAS_PROVISIONER:
    from provisioner._api_cli import api_args_to_cli
    from provisioner.api_spec import api_spec


def __virtual__():
    '''
    only load cheese if enzymes are available
    '''
    if HAS_PROVISIONER:
        return __virtualname__
    else:
        return (
            False,
            (
                'The provisioner execution module cannot be loaded:'
                ' provisioner package unavailable.'
            )
        )


# TODO generate docs
def _api_wrapper(fun):
    def f(*args, **kwargs):
        _kwargs = {k: v for k, v in kwargs.items() if not k.startswith('__')}
        _kwargs['loglevel'] = 'INFO'
        _kwargs['logstream'] = 'stderr'
        _kwargs['output'] = 'json'
        cli_args = api_args_to_cli(fun, *args, **_kwargs)
        cmd = ' '.join(['provisioner'] + cli_args)
        res = __salt__['cmd.run'](cmd)
        import json
        return json.loads(res)
    return f


for fun in api_spec:
    setattr(mod, fun, _api_wrapper(fun))
