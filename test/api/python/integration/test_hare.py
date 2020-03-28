import pytest

test_status_offline_fname = 'pcs.status.offline.out'
test_status_online_fname = 'pcs.status.online.out'
test_stop_fname = 'pcs.cluster.stop.all.out'
test_start_fname = 'pcs.cluster.start.all.out'


pcs_mock_tmpl = '''
    if [[ "$1 $2" == "cluster stop" ]]; then
        cat {stop_out}
    elif [[ "$1 $2" == "cluster start" ]]; then
        cat {start_out}
        echo 1 >/tmp/pcs.starting
    elif [[ "$1" == 'status' ]]; then
        if [[ -f /tmp/pcs.starting ]]; then
            try="$(cat /tmp/pcs.starting)"
            try=$(( $try + 1 ))
            echo $try >/tmp/pcs.starting

            if [[ "$try" -gt 5 ]]; then
                cat {status_online_out}
            else
                cat {status_offline_out}
            fi
        else
            cat {status_offline_out}
        fi
    else
        echo "Unexpected args: <$@>"
        exit 1
    fi
'''


@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_cluster_mgmt(
    mhosteosnode1, run_test, request, test_output_dir
):
    pcs_mock = pcs_mock_tmpl.format(
        stop_out=mhosteosnode1.copy_to_host(
            test_output_dir / test_stop_fname
        ),
        start_out=mhosteosnode1.copy_to_host(
            test_output_dir / test_start_fname
        ),
        status_offline_out=mhosteosnode1.copy_to_host(
            test_output_dir / test_status_offline_fname
        ),
        status_online_out=mhosteosnode1.copy_to_host(
            test_output_dir / test_status_online_fname
        )
    )
    request.applymarker(pytest.mark.mock_cmds(
        {'eosnode1': [{'pcs': pcs_mock}]})
    )
    request.getfixturevalue('mock_hosts')
    run_test(mhosteosnode1)
