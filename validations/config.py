FACTORY_POST_CHECK = {
    'verify_nodes_connectivity': 'ServerValidations',
    'verif_node_communication': 'ServerValidations',
    'verify_mgmt_vip': 'NetworkChecks',
    'verify_cluster_ip': 'NetworkChecks',
    'verify_public_data_ip': 'NetworkChecks',
    'verify_private_data_ip': 'NetworkChecks',
    'verify_luns_consistency': 'StorageValidations',
    'verify_access_to_controller': 'ControllerValidations',
    'verify_passwordless': 'ServerValidations',
    'verify_lvm': 'LVMChecks'
}

FACTORY_PRE_CHECK = {
}

REPLACE_NODE_CHECK = {
    'verify_mgmt_vip': 'NetworkChecks',
    'verify_luns_consistency': 'StorageValidations'
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
            UNBOXING_CHECK):
    ALL_CHECKS.update(check)
