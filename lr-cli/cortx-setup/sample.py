# Sample of expected Node Signature for stamping

>>> for node in pillar['node']:
...  pillar['node'][node]['signature'] = node + 'ABC'
...
>>> pillar['node']
{'srvnode-1': {'hostname': 'localhost-1', 'signature': 'srvnode-1ABC'}, 'srvnode-2': {'hostname': 'localhost-2', 'signature': 'srvnode-2ABC'}}
