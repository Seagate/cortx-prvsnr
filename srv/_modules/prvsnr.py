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

import sys

# HOW TO DEBUG:
# - set a breakpoint: import pdb; pdb.set_trace()
# - salt-run saltutil.sync_modules
# - salt-run salt.cmd provisioner.<fun> ... <args>

__virtualname__ = 'provisioner'

try:
    import provisioner
except ImportError:
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


# TODO generate docs
def _api_wrapper(fun):
    from provisioner._api_cli import api_args_to_cli
    from shlex import quote

    # TODO subprocess.list2cmdline is an another option
    #      but it is not documented as API

    def f(*args, **kwargs):
        _kwargs = {k: v for k, v in kwargs.items() if not k.startswith('__')}

        _kwargs['noconsole'] = True
        _kwargs['rsyslog'] = True
        _kwargs['rsyslog-level'] = 'DEBUG'
        _kwargs['rsyslog-formatter'] = 'full'

        # don't make sense here
        for k in ('nowait', 'username', 'password', 'eauth'):
            _kwargs.pop(k, None)

        # turn off salt job mode as well to prevent infinite api loop
        env = {
            'PRVSNR_SALT_JOB': 'no',
            'PRVSNR_OUTPUT': 'json'
        }

        cmd = ['provisioner']
        cmd.extend(api_args_to_cli(fun, *args, **_kwargs))
        cmd = [quote(p) for p in cmd]
        return __salt__['cmd.run'](' '.join(cmd), env=env)

    return f


if HAS_PROVISIONER:
    from provisioner.api_spec import api_spec
    mod = sys.modules[__name__]
    for fun in api_spec:
        setattr(mod, fun, _api_wrapper(fun))


def __virtual__():
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
