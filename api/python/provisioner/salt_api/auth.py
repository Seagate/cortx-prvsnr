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

import logging


logger = logging.getLogger(__name__)


_eauth = 'pam'
_username = None
_password = None


def username():
    return _username


def password():
    return _password


def eauth():
    return _eauth


# TODO
#   - think about static salt client (one for the module)
def auth_init(username, password, eauth='pam'):
    global _eauth
    global _username
    global _password
    _eauth = eauth
    _username = username
    _password = password


# TODO TEST
def _set_auth(kwargs):
    eauth = kwargs.pop('eauth', _eauth)
    username = kwargs.pop('username', _username)
    password = kwargs.pop('password', _password)

    if username:
        kwargs['eauth'] = eauth
        kwargs['username'] = username
        kwargs['password'] = password

    return
