# CHECK_ARG = {'function_implemented': 'Class_implemented_in'}

FACTORY_PRE_CHECK = {
    'mlnx_ofed_installed': 'HardwareValidations',
    'mlnx_hca_present': 'HardwareValidations',
    'lsb_hba_present': 'HardwareValidations',
    'lsb_hba_req_ports': 'HardwareValidations',
    'volumes_accessible': 'StorageValidations',
    'volumes_mapped': 'StorageValidations'   #TO DO: Verify and move this to post-check
}

FACTORY_POST_CHECK = {
    'corosync_status': 'ClusterValidations',
    'nodes_status': 'ClusterValidations',
    'get_resource_failcount': 'ClusterValidations',
    'cluster_status': 'ClusterValidations',
    'stonith_issues': 'ClusterValidations',
    'bmc_accessible': 'BMCValidations',
    'consul_check': 'CortxValidations',
    'elasticsearch_check': 'CortxValidations',
    'ioservice_check': 'CortxValidations',
    'verify_nodes_online': 'ServerValidations',
    'verif_node_communication': 'ServerValidations',
    'verify_mgmt_vip': 'NetworkChecks',
    'verify_cluster_ip': 'NetworkChecks',
    'verify_public_data_ip': 'NetworkChecks',
    'verify_private_data_ip': 'NetworkChecks',
    'verify_luns_consistency': 'StorageValidations',
    'verify_access_to_controller': 'ControllerValidations',
    'verify_passwordless': 'ServerValidations',
    'verify_lvm': 'StorageValidations'
}


REPLACE_NODE_CHECK = {
}

FW_UPDATE_CHECK = {
}

UNBOXING_CHECK = {
}

ALL_CHECKS = {
}

for check in (
            FACTORY_POST_CHECK,
            FACTORY_PRE_CHECK,
            REPLACE_NODE_CHECK,
            FW_UPDATE_CHECK,
            UNBOXING_CHECK ):
    ALL_CHECKS.update(check)
