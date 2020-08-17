import os
import yaml
import logging
import subprocess

log = logging.getLogger(__name__)

def sync_files(component = "provisioner", replace_node = False):
    yaml_file = '/opt/seagate/cortx/{0}/conf/setup.yaml'.format(component)
    if not os.path.exists(yaml_file):
        print("ERROR: {0} doesn't exist.".format(yaml_file))
        return False

    node = __grains__["id"]
    if not replace_node:
        replace_node = os.getenv("NODE_REPLACED", False)

    if not replace_node:
        if node == "srvnode-1": node = "srvnode-2"
        else: node = "srvnode-1"
    else:
        node_list = __pillar__["cluster"]["node_list"]
        node_list.remove(node)
        node = node_list[0]

    with open(yaml_file, 'r') as fd:
        yaml_dict = yaml.safe_load(fd)

    if "backup" in yaml_dict[component] and "files" in yaml_dict[component]["backup"]:
        cmd = "rsync -zavhe ssh"
        for file in yaml_dict[component]["backup"]["files"]:
            log.info(
                subprocess.run(
                    ["{0} {1}:{2} {2}".format(cmd,node,file)],
                    shell = True,
                    stdout = subprocess.PIPE
                )
            )
    return True

