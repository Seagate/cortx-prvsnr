#!/usr/bin/python3

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
    """ get csm admin user from consul """
    users = _get_all_csm_users(args.i, args.c)
    if isinstance(users, list):
        for user in users:
            if user:
                user_id = _check_if_admin_user(user, args.c)
            if user and user_id :
                print(f"*** creating admin user {user_id} ***")
                create_user(user_id, "")


if __name__=='__main__':      
    import argparse
    import provisioner    

    argParser = argparse.ArgumentParser()
    argParser.add_argument("-c", type=str, default="/opt/seagate/cortx/hare/bin/consul",
            help="Path to consul binary default : /opt/seagate/cortx/hare/bin/consul")
    argParser.add_argument("-i", type=str, default="eos/base/user_collection/obj/",
            help="Key to User collection in csm default : eos/base/user_collection/obj/ ")
    argParser.set_defaults(func=get_admin_user)
    args = argParser.parse_args()
    args.func(args)
    sys.exit(0)



