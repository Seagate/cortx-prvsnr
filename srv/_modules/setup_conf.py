# How to test:
# salt-call saltutil.clear_cache && salt-call saltutil.sync_modules
# salt-call setup_conf.conf_cmd "../files/samples/setup.yaml" 'test:post_install'
import errno
import os
import yaml


def conf_cmd(conf_file, conf_key):
    if not os.path.exists(conf_file):
        print("[ERROR   ] Setup config file {0} doesn't exist.".format(conf_file))
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            conf_file
        )

    # print("Setup config file {0}".format(conf_file))

    ret_val = ''
    with open(conf_file, 'r') as fd:
        try:
            yml_dict = yaml.safe_load(fd)

            script_path = yml_dict[conf_key.split(':')[0]][conf_key.split(':')[1]]['script']
            if script_path and os.path.exists(script_path):
                args = yml_dict[conf_key.split(':')[0]][conf_key.split(':')[1]]['args']
                if isinstance(args, list):
                    args = ' '.join(args)

                ret_val = script_path + " " + str(args)

        except yaml.YAMLError as ymlerr:
            print("Error parsing yaml file {0}".format(ymlerr))
            ret_val = None

    return ret_val
