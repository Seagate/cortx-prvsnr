# CLI_ARG = {'function_implemented': 'Class_implemented_in'}

FACTORY_PRE_CHECK = {
    'mlnx_ofed_installed': 'PreFactoryValidations',
    'mlnx_hca_present': 'PreFactoryValidations',
    'lsb_hba_present': 'PreFactoryValidations',
    'volumes_accessible': 'PreFactoryValidations',
    'volumes_mapped': 'PreFactoryValidations'    #TO DO: Verify and move this to post-check 
}

FACTORY_POST_CHECK = {
    'verify_corosync_status': 'PacemakerValidations',
    'verify_nodes_status': 'PacemakerValidations',
    'get_resource_failcount': 'PacemakerValidations',
    'verify_cluster_status': 'PacemakerValidations',
    'check_stonith_issues': 'PacemakerValidations',
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


SW_UPDATE_CHECK = {
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
            SW_UPDATE_CHECK,
            FW_UPDATE_CHECK,
            UNBOXING_CHECK ):
    ALL_CHECKS.update(check)
