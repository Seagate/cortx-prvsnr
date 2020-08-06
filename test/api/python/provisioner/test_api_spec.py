#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

from provisioner.api_spec import (
    process_param_spec, PILLAR_PATH_KEY, PARAM_TYPE_KEY, param
)


def test_process_param_spec():
    spec = {
        'group1': {
            PILLAR_PATH_KEY: 'path1.sls',
            'attr1': 'key/path/attr1',
            'attr2': 'key/path/attr2',
        },
        'group2': {
            PILLAR_PATH_KEY: 'path2.sls',
            'attr3': 'key/path/attr3',
            'subgroup21': {
                PILLAR_PATH_KEY: 'path3.sls',
                'attr4': 'key/path/attr4'
            }
        },
        'dict': {
            PILLAR_PATH_KEY: 'path4.sls',
            'item1': {
                PARAM_TYPE_KEY: 'ParamDictItem',
                'parent': 'key/path/attr5',
                'key': 'key_name',
                'value': 'value_name'
            },
            'item2': {
                PARAM_TYPE_KEY: 'ParamDictItem',
                'parent': 'key/path/attr5'
            }
        }
    }

    res = process_param_spec(spec)

    params = [
        param.Param('group1/attr1', ('key/path/attr1', 'path1.sls')),
        param.Param('group1/attr2', ('key/path/attr2', 'path1.sls')),
        param.Param('group2/attr3', ('key/path/attr3', 'path2.sls')),
        param.Param(
            'group2/subgroup21/attr4', ('key/path/attr4', 'path3.sls')
        ),
        param.ParamDictItem(
            'dict/item1', ('key/path/attr5', 'path4.sls'),
            'key_name', 'value_name'
        ),
        param.ParamDictItem(
            'dict/item2', ('key/path/attr5', 'path4.sls'),
            'pillar_key', 'pillar_value'
        )
    ]

    expected = {str(p.name): p for p in params}
    assert res == expected
