import os
import yaml
import subprocess
from cortx import _read_yaml

def sync_files(component = "provisioner", replace_node = False):
    yaml_file = '/opt/seagate/cortx/{0}/conf/setup.yaml'.format(component)
    if not os.path.exists(yaml_file):
        print("ERROR: {0} doesn't exist.".format(yaml_file))
        return False

    node = __grains__["id"]
    if not replace_node:
        replace_node = os.getenv("NODE_REPLACED", False)
        node_list = __pillar__["cluster"]["node_list"]
        node_list.remove(node)
        node = node_list[0]
    if not replace_node:
        if node == "srvnode-1": node = "srvnode-2"
        else: node = "srvnode-1"
        
   
    yaml_dict = _read_yaml(yaml_file)
    if yaml_dict[component]["backup"] and yaml_dict[component]["backup"]["files"]:
        cmd = "rsync -zavhe ssh"
        for file in yaml_dict[component]["backup"]["files"]:
            subprocess.run(
                cmd.append(" {0}:{1} {1}".format(node,file)),
                shell = True,
                stdout = subprocess.PIPE
            )
    return True
      
      



