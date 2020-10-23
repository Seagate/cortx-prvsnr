# CHECK_ARG = {'function_implemented': 'Class_implemented_in'}

FACTORY_PRE_CHECK = {
    'check_mlnx_ofed_installed': 'PreFlightValidationsCall',
    'check_mlnx_hca_present': 'PreFlightValidationsCall',
    'check_mlnx_hca_req_ports': 'PreFlightValidationsCall',
    'check_lsb_hba_present': 'PreFlightValidationsCall',
    'check_lsb_hba_req_ports': 'PreFlightValidationsCall',
    'check_volumes_accessible': 'PreFlightValidationsCall',
    'check_volumes_mapped': 'PreFlightValidationsCall'   #TO DO: Verify, if needed, move to post-check
}

FACTORY_POST_CHECK = {
    'check_corosync_status': 'ClusterValidationsCall',
    'check_nodes_status': 'ClusterValidationsCall',
    'check_get_resource_failcount': 'ClusterValidationsCall',
    'check_cluster_status': 'ClusterValidationsCall',
    'check_stonith_issues': 'ClusterValidationsCall',
    'check_bmc_accessible': 'ClusterValidationsCall',
    'check_consul_check': 'CortxValidationsCall',
    'check_elasticsearch_check': 'CortxValidationsCall',
    'check_ioservice_check': 'CortxValidationsCall',
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
    'check_stonith_issues': 'UnboxingValidationsCall',
    'check_bmc_accessible': 'UnboxingValidationsCall',
    'check_controller_mc_accessible': 'UnboxingValidationsCall'
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
