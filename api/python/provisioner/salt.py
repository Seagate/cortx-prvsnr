from salt.client import LocalClient
from pprint import pprint

from .errors import SaltError

_eauth = 'pam'
_username = None
_password = None

# TODO
#   - think about static salt client (one for the module)

def auth_init(username, password, eauth='pam'):
    global _eauth
    global _username
    global _password
    _eauth = eauth
    _username = username
    _password = password



# salt full return format (TODO ??? salt docs for that)
"""
{
    '<target>': {
        'jid': '<jid>',
        'out': '<output-format>',
        'ret': {
            '<task-id-key>': {
                '__id__': '<task-string-id>'
                '__run_num__': 1,
                '__sls__': '<state-path-dotted>',
                'changes': {<changes dict>},
                'comment': '<human-readable-comment>',
                'duration': 37.465,
                ...
                'result': True,
                'start_time': '13:34:30.645186'
            },
            ...
        },
        'retcode': 0
    }
}
"""


def _salt_client_cmd(*args, **kwargs):
    if _username or 'username' in kwargs:
        kwargs['eauth'] = kwargs.get('eauth', _eauth)
        kwargs['username'] = kwargs.get('username', _username)
        kwargs['password'] = kwargs.get('password', _password)

    try:
        res = LocalClient().cmd(*args, full_return=True, **kwargs)
    except Exception as exc:
        # TODO too generic
        raise SaltError(str(exc))

    # TODO is it a valid case actually ?
    if type(res) is not dict:
        return res

    results = {}
    fails = {}
    for target, job_result in res.items():
        ret = job_result['ret']
        results[target] = ret

        _fails = {}
        if job_result['retcode'] != 0:
            salt_fun = args[1]
            if str(salt_fun).startswith('state.') and type(ret) is dict:
                for task, tresult in ret.items():
                    if not tresult['result']:
                        _fails[task] = tresult['comment']
            else:
                _fails = ret

        if _fails:
            fails[target] = _fails

    if fails:
        # TODO better logging
        pprint(res)
        # TODO add res to exception data
        raise SaltError(
            "salt command failed: {}".format(fails)
        )

    return results


def pillar_get(targets='*'):
    return _salt_client_cmd(targets, 'pillar.items')


def pillar_refresh(targets='*'):
    return _salt_client_cmd(targets, 'saltutil.refresh_pillar')


def states_apply(states, targets='*'):
    ret = {}

    for state in states:
        # TODO multiple states at once
        try:
            res = _salt_client_cmd(targets, 'state.apply', [state])
        except SaltError as exc:
            raise SaltError(
                "Failed to apply state '{}': {}"
                .format(state, str(exc))
            )
        else:
            ret[state] = res

    return ret
