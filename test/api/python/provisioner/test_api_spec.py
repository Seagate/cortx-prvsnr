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
        param.Param('group1/attr1', 'path1.sls', 'key/path/attr1'),
        param.Param('group1/attr2', 'path1.sls', 'key/path/attr2'),
        param.Param('group2/attr3', 'path2.sls', 'key/path/attr3'),
        param.Param('group2/subgroup21/attr4', 'path3.sls', 'key/path/attr4'),
        param.ParamDictItem(
            'dict/item1', 'path4.sls', 'key/path/attr5',
            'key_name', 'value_name'
        ),
        param.ParamDictItem(
            'dict/item2', 'path4.sls', 'key/path/attr5',
            'pillar_key', 'pillar_value'
        )
    ]

    expected = {str(p.name): p for p in params}
    assert res == expected
