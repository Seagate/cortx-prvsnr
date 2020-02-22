def install_provisioner_api(mhost):
    mhost.check_output("pip3 install {}".format(mhost.repo / 'api/python'))
