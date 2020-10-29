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
#    'check_stonith_issues': 'ClusterValidationsCall',  #TO DO: verify alternative for log files check
    'check_bmc_accessible': 'ClusterValidationsCall',
    'check_consul_service': 'CortxValidationsCall',
    'check_elasticsearch_service': 'CortxValidationsCall',
    'check_ioservice_service': 'CortxValidationsCall'
}


REPLACE_NODE_CHECK = {
}

FW_UPDATE_CHECK = {
}

UNBOXING_CHECK = {
    'verify_public_data_interface_ip': 'NetworkChecks',
    'check_bmc_accessible': 'ClusterValidationsCall',
    'check_controller_mc_accessible': 'UnboxingValidationsCall',
    'check_bmc_stonith_config': 'UnboxingValidationsCall'
}

#UNBOXING_POST_CHECK = {
#    'check_stonith_issues': 'ClusterValidationsCall'
#}

ALL_CHECKS = {
}

for check in (
            FACTORY_POST_CHECK,
            FACTORY_PRE_CHECK,
            REPLACE_NODE_CHECK,
            FW_UPDATE_CHECK,
            UNBOXING_CHECK ):
    ALL_CHECKS.update(check)
