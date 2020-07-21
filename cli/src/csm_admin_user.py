#!/usr/bin/python3

# test this using command : python3 csm_admin_user.py -n <srvnode-2>

#usage: csm_admin_user.py [-h] [-c C] [-i I] [-n N]
#
#optional arguments:
#  -h, --help  show this help message and exit
#  -c C        Path to consul binary default :
#              /opt/seagate/cortx/hare/bin/consul
#  -i I        Key to User collection in csm default :
#              eos/base/user_collection/obj/
#  -n N        node_id of replacing node i.e. srvnode-1/srvnode-2
 
import subprocess
import json
import sys

def _run_command(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, shell=True)
    if res.returncode:
       print(f"failed to run command {cmd} ")
       return res.stderr
    else:
       if res.stdout:
           return res.stdout.decode("utf-8")

def _get_node_list():
    res = _run_command(f" salt-call pillar.get cluster:node_list --out=json ")
    result = json.loads(res)
    return result["local"]

def _get_all_csm_users(user_key, consul_path):
    res = _run_command(f"{consul_path} kv get -keys {user_key}")
    users = res.split("\n")
    return users

def _check_if_admin_user(user_key, consul_path):
    res = _run_command(f"{consul_path} kv get {user_key}")
    user = json.loads(res)
    if "admin" in user["roles"]:
        return user["user_id"]
    else:
        return False

def create_user(uname, password ):
    """ create linux user using privisioner api """
    return provisioner.create_user(uname=uname, passwd=password)

def get_admin_user(args):
    """ sync csm admin user from active node to replace node"""
    users = _get_all_csm_users(args.i, args.c)
    if isinstance(users, list):
        print("*** Retrieving csm admin user from consul***")
        for user in users:
            if user:
                user_id = _check_if_admin_user(user, args.c)
            if user and user_id :
                print(f"*** creating admin user {user_id} on {args.n} ***")
                create_user(user_id, "")
                nodes = _get_node_list()
                nodes.remove(args.n)
                if len(nodes) > 0:
                    print(f"Active node is {nodes[0]}")
                    password = _get_password(nodes[0], user_id)
                    _update_password(args.n, user_id, password)

def _get_password(node_id, user_id):
    res = _run_command(f" salt {node_id} cmd.run 'grep {user_id} /etc/shadow' --out=json ")
    result = json.loads(res)
    data = result[node_id]
    data_a = data.split(":")
    passwd = data_a[1]
    return passwd.replace("$","\$")

def _update_password(node_id, user_id, passwd):
    print("*** Sync up password with active node *** ")
    res = _run_command(f" salt {node_id} cmd.run 'usermod {user_id} --password {passwd}' --out=json ")
    result = json.loads(res)
    if result[node_id] == "":
        print("Admin user password set successfully") 

if __name__=='__main__':      
    import argparse
    import provisioner    

    argParser = argparse.ArgumentParser()
    argParser.add_argument("-c", type=str, default="/opt/seagate/cortx/hare/bin/consul",
            help="Path to consul binary default : /opt/seagate/cortx/hare/bin/consul")
    argParser.add_argument("-i", type=str, default="eos/base/user_collection/obj/",
            help="Key to User collection in csm default : eos/base/user_collection/obj/ ")
    argParser.add_argument("-n", type=str,
            help="node_id of replacing node i.e. srvnode-1/srvnode-2")
    argParser.set_defaults(func=get_admin_user)
    args = argParser.parse_args()
    args.func(args)
    sys.exit(0)
