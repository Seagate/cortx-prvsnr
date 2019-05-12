#!/bin/bash

script_dir=$(dirname $0)
source $script_dir/eos-defs.sh

cs_tmpfile="/tmp/mero_status"
timeout_cmd=/usr/bin/timeout
timeout=30s

ask_yes_no()
{
    if [ "$1" = "-y" ]; then
        return 0
    fi
    while true; do
        echo -e "\n$1"
        echo "y=Proceed with operation, n=exit"
        read -p "Proceed? [y/n]:" proceed
        if [ "$proceed" = "y" ]; then
            return 0
        elif [ "$proceed" = "n" ]; then
            echo "Exiting"
            exit 0
        fi
    done
}

ask_yes_no_skip()
{
    if [ "$1" = "-y" ]; then
        echo "$2"
        return 0
    fi
    while true; do
        echo "$1"
        echo "y=Proceed with operation, n=stop & exit, skip=skip only this step"
        read -p "Proceed? [y/n/skip]:" proceed
        if [ "$proceed" = "y" ]; then
            return 0
        elif [ "$proceed" = "n" ]; then
            echo "Exiting"
            exit 0
        elif [ "$proceed" = "skip" ]; then
            echo "Skipping this step"
            return 2
        fi
    done
}

print_warning()
{
    echo ""
    echo "======================== WARNING ================================"
    echo ""
    echo " This is dangerous operation, it will stop the S3 mero cluster"
    echo " and all mero/halon services across the cluster nodes. This may"
    echo " result in loss of data on the mero object store."
    echo ""
    echo "================================================================="
    ask_yes_no $1 "Proceed wisely"
    if [ $? -eq 1 ]; then
        exit 0
    fi
}

bootstrap_util_usage()
{
    echo "usage: $0 [-y] [-c <eos-config-file.yaml>]" \
        "[-e <data network inerface> [-E <mgmt network interface>]]"
    exit 1
}

# Get status of halond service
# Retrun values:
# 0 service is online
# 1 service is offline
# 2 for multinode cluster, halond is active
#   on some nodes and inactive on others.
cluster_halond_status_get()
{
    local tmpfile="/tmp/hs"
    if [ $single_node_cluster = "no" ]; then
        $pdsh_all_nodes systemctl status halond | grep Active | awk '{ print $3}' 2>&1 | tee $tmpfile
        if grep -q -w "active" $tmpfile
        then
            #Check if some are active and some inactive
            if grep -q -w "inactive" $tmpfile; then return 2; else return 0; fi;
        else
            #inactive
            return 1
        fi
    else
        echo "Checking status of halond service.."
        halond_status="$(systemctl status halond | grep Active | awk '{ print $2}')"
        [ $halond_status = "active" ] && return 0 || return 1
    fi
}

cluster_halond_start()
{
    # Check and Start halond service.
    cluster_halond_status_get
    case $? in
        0)
            echo "halond service is active"
            return 0
            ;;
        1)
            #halond is inactive or failed
            echo "halond service is not active"
            echo "Starting halond now.."
            $pdsh_all_nodes systemctl start halond
            ;;
        2)
            #on some nodes halond is active, on some inactive.
            #It is difficult to identify the nodes where it is
            #inactive, so start on all nodes.
            echo "On some node(s) halond is inactive."
            echo "Restarting halond on all nodes now.."
            $pdsh_all_nodes systemctl restart halond
            ;;
    esac
    cluster_halond_status_get
    if [ $? -ne 0 ]; then
        [ $single_node_cluster = "yes" ] && echo "Could not start halond" ||
            echo "Could not start halond on all nodes, check status of halond on each node"
        return 1
    fi
    echo "halond service started successfully"
    return 0
}

# Return values
# 0 Cluster is online
# 1 Cluster is offline
# 2 Cluster is in failed state
# 3 Status command timed out after 30s
cluster_status_get()
{
    echo "---- Getting cluster status ----"
    if [ $single_node_cluster = "no" ]; then
        $pdsh_RC_host $timeout_cmd $timeout hctl mero status 2>&1 | tee $cs_tmpfile
        tail -1 $cs_tmpfile | grep -q 124 2>&1 >/dev/null
        [ $? -eq 0 ] && return 3 #timed out, assume cluster is stopped.
    else
        $timeout_cmd $timeout hctl mero status
        ret=$?
        #timeed out, assume cluster is stopped.
        [ $ret -eq 124 ] && echo "timed out" && return 3
        [ $ret -eq 1 ] && echo "timed out" && return 1
        $timeout_cmd $timeout hctl mero status > $cs_tmpfile
    fi

    #Check if cluster is in failed state.
    grep -q -E "failed|inhibited" $cs_tmpfile && return 2

    grep -q "node disconnected" $cs_tmpfile && return 1

    #TODO: Fix this ugly if-else
    if [ $single_node_cluster = "no" ]; then
        clust_status=$($pdsh_RC_host "$timeout_cmd $timeout hctl mero status --json" \
            "| jq -r .csrStatus._mcs_disposition")
        cs=$(echo $clust_status | awk '{ print $2 }')
    else
        clust_status=$($timeout_cmd $timeout hctl mero status --json | \
            jq -r .csrStatus._mcs_disposition)
        cs=$clust_status
    fi

    # In case 'hctl mero status' timed out the cluster_status will be empty.
    [ -z $cs ] && return 1

    [ $cs = "ONLINE" ] && return 0 || return 1
}

cluster_stop_and_cleanup()
{
    cluster_stop $1
    cluster_cleanup_data $1
}

cluster_stop()
{
    local yn=$1
    local halond_stopped="false"
    print_warning $yn

    cluster_halond_status_get
    [ $? -eq 1 ] && halond_stopped="true"

    if [ $halond_stopped = "false" ]; then
        #halond is online, stop the cluster first.
        cluster_status_get;
        ret=$?
        case $ret in
            0 | 2)
                # Online of in failed state
                ask_yes_no_skip $yn "---- Stopping the cluster ----"
                $pdsh_RC_host $timeout_cmd $timeout hctl mero stop
                ;;
            1 | 3)
                # Offline or status command timed out
                echo "Cluster is offline"
                ;;
        esac
    fi
}

cluster_cleanup_data()
{
    local yn=$1
    ask_yes_no_skip $yn "---- Cleaning up existing halond data -----"
    [ $? -eq 0 ] && $pdsh_all_nodes systemctl start halon-cleanup
    ask_yes_no_skip $yn "---- Cleaning up existing mero data -----"
    if [ $? -eq 0 ]; then
        echo "This might take little long, be patient"
        $pdsh_all_nodes systemctl start mero-cleanup
    fi
    echo "---- Stopping lnet service ----"
    $pdsh_all_nodes systemctl stop lnet

    echo -e "cleanup done\n"
    return 0
}

cluster_bootstrap()
{
    local yn=$1
    echo "------ Bootstrapping the EOS cluster ------"
    echo "************** Warnig *********************"
    echo "* This operation bootstraps the cluster & *"
    echo "* will erase all the data stored on EOS.  *"
    ask_yes_no_skip $yn "Proceed wisely"
    if [ $do_genfacts = "true" ]; then
        # Generate config files only when
        # mini cluster conf file is provided,
        # else justre-bootstrap the cluster
        # with existing config files.
        cluster_netinfo_get
        generate_halon_facts
        echo "Checking halon conf file.."
        generate_halond_conf
        echo "Chekcing LNet configuration.."
        lnet_conf_create
    fi
    echo "Starting Halond"
    cluster_halond_start
    [ $? -eq 1 ] && { echo "run 'systemctl status halond' to know more."; exit 1; }

    ask_yes_no $yn "---- Ready to start the bootstrap process.. ----"
    if [ $? -eq 0 ]; then
        echo -e "Bootstrapping the EOS cluster.\n"
        $pdsh_RC_host hctl mero bootstrap -v
        $pdsh_RC_host hctl mero status
    fi
    if [ $single_node_cluster = "no" ]; then
        #Make client nodes join the cluster
        cluster_add_client_nodes
    fi
    echo "Waiting for the cluster to come online"
    sleep 1m
    $pdsh_RC_host hctl mero status

    echo ""
    echo "EOS bootstrap done"
    echo "Bringing up all the EOS services might take some time."
    echo "Run 'hctl mero status' to check EOS status and ensure" \
        "all services are oniline before using it."
    return 0
}

cluster_netinfo_get()
{
    echo -e "\nChecking Network information provided"
    if [ -z $net_if ]; then
        if [ $single_node_cluster = "no" ]; then
            echo "This is multinode setup, please provide the network" \
                "interface"
            echo "If you want to have separate interfaces for data and" \
                "management interfaces, you can use -e <data interface> -E"\
                "<mgmt interface> option."
            echo "Also, ensure the interface names are uniform across all" \
                "the nodes."
            bootstrap_util_usage
        fi
        echo "Network interface not provided"
        echo "Checking if existing interfaces can be used.."
        net_if=$(ip -oneline -4 address show scope global up | \
            grep -v docker | tail -n 1 | awk '{print $2}')
        [ -z $net_if ] && echo "Error: Could not find the usable" \
            "network interface, configure the network interace and" \
            "rerun the command" && exit 1
        echo "Found the following network interface: $net_if"
        echo "Using $net_if as a default interface"
    fi
    [ -z $mgmt_if ] && echo -e "\nManagement interface not provided, using" \
        "the data interface provided:$net_if " && mgmt_if=$net_if
    net_if_ip="$(ip a show $net_if | grep "\<inet\>" | awk '{print$2}' | \
        cut -f1 -d "/")"
    mgmt_if_ip="$(ip a show $mgmt_if | grep "\<inet\>" | awk '{print$2}' | \
        cut -f1 -d "/")"
    echo "------------------------------------------------------"
    echo "Data network interface              = $net_if"
    echo "Management network interface        = $mgmt_if"
    [ $single_node_cluster = "yes" ] && {
        echo "Data interface ip address       = $net_if_ip";
        echo "management interface ip address = $mgmt_if_ip";
    }
    echo -e "------------------------------------------------------\n"
}

cluster_lnet_dignose_and_fix()
{
    #TODO: Will only work for single node cluster
    [ $single_node_cluster = "no" ] && {
        echo "This operation is not supported on multinode cluster";
        exit 1;
    }

    # Check if lnid is up
    # if up, check ip is of the data interface
    # if ip doesn't match then regenerate lnet
    # conf file with correct ip and restart lnet.

    echo "Checking LNet configuration"
    lnid="$(lctl list_nids)"
    [ $lnid = "$net_if_ip@tcp" ] && echo "lnid is up: $lnid" \
        || echo "lnid is not up."

    echo "Checking the LNet config file"
    lnet_conf_create
    echo "startig LNet network"
    systemctl restart lnet
    lnid="$(lctl list_nids)"
    if [ $lnid = "$net_if_ip@tcp" ]; then
        echo "lnid is up: $lnid"
        echo "Stopping LNet service now, it will be" \
            "started again when halond is restarted"
        return 0
    fi
    echo "lnids could not be listed with data network interface," \
        "try rebooting the machine"
    echo "Stopping LNet"
    systemctl stop lnet
    return 1
}

lnet_conf_create()
{
    #TODO: Will only work for single node cluster
    [ $single_node_cluster = "no" ] && {
        echo "This operation is not supported on multinode cluster";
        echo "Create $lnet_conf on all the nodes"
        echo "and run 'hctl mero bootstrap' command"
        echo "to bootstrap the cluster"
        exit 1;
    }

    if ! grep -q lnet /etc/modprobe.d/* ; then
        echo "No LNet config file found"
        echo "Generating LNet config /etc/modprobe.d/lnet.conf"
        echo "options lnet networks=tcp($net_if) config_on_load=1" \
            > $lnet_conf
        echo "Lnet conf file created successfully."
        return 0
    elif ! grep -q "lnet.*$net_if" /etc/modprobe.d/* ; then
        echo -e "looks like LNet isn't configured on $net_if interface:\n" \
            "  $(grep lnet /etc/modprobe.d/*)\n" \
            " Correcting the config file with data network interface"
        echo "options lnet networks=tcp($net_if) config_on_load=1" > $lnet_conf
        echo "Lnet conf file updated successfully."
        return 0
    fi
}

cluster_lnet_service_start()
{
    #TODO: Will only work for single node cluster
    [ $single_node_cluster = "no" ] && {
        echo "This operation is not supported on multinode cluster";
        exit 1;
    }

    ## Start lnet service
    echo "Checking lnet service"
    lnet_status="$(systemctl status lnet  | grep Active | awk '{ print $2}')"
    if [ $lnet_status = "active" ]; then
        echo "LNet serice is already started."
        return 0
    fi
    echo "LNet is not active.. restarting lnet service"
    systemctl start lnet
    lnet_status1="$(systemctl status lnet  | grep Active | awk '{ print $2}')"
    if [ $lnet_status1 != "active" ]; then
        echo "LNet is not started, run 'systemctl status lnet' to know more"
        return 1
    fi
    echo "LNet service started successfully"
    return 0
}

generate_halond_conf()
{
    #TODO: Make this working for multinode cluster
    [ $single_node_cluster = "no" ] && {
        echo "This operation is not supported on" \
            "multinode cluster yet"
        echo "Create $halond_conf on all the nodes"
        echo "and run 'hctl mero bootstrap' command"
        echo "to bootstrap the cluster"
        exit 1
    }

    if [ -e $halond_conf ]; then
        grep -q $mgmt_if_ip $halond_conf || \
            echo "halond is not configured with mgmt ip $mgmt_if_ip"
    fi
    echo "Generating $halond_conf"
    echo "HALOND_LISTEN=$mgmt_if_ip:9070" > $halond_conf
    echo "Generated $halond_conf successfully"
    cat $halond_conf
    return 0
}

generate_halon_facts()
{
    netif_opt="-e $net_if -E $mgmt_if"
    output_file_opt="-o $halon_facts"
    input_file_opt="-c $mini_conf"
    parity_grp_opt="-N $n_data_units -K $n_parity_units"
    genfacts_opt="$input_file_opt $output_file_opt $netif_opt $parity_grp_opt"

    if $pdsh_RC_host stat $halon_facts > /dev/null
    then
        echo "Backing up old halon facts file"
        $pdsh_RC_host cp $halon_facts $halon_facts.bkp.$(date +%F_%R)
        echo "Previous halond facts file is backed up as:" \
            "$halon_facts.bkp.$(date +%F_%R)"
    else
        echo -e "\nNo halon facts file $halon_facts found."
    fi
    echo -e "Generating halon facts file, it might take some time, be patient."
    m0genfacts $genfacts_opt -v
    [ $? -ne 0 ] && echo "Error generating halon facts file, exiting" && exit 1
    echo "Halon facts file generated succefully."
    if [ $single_node_cluster = "no" ]; then
        echo "Copying it to $RC_host:$halon_facts"
        scp $halon_facts root@$RC_host:$halon_facts
        [ $? -ne 0 ] && echo "Error copying halon_facts to " \
            "$RC_host:$halon_facts" \ && exit 1
    fi
}

cluster_mero_start()
{
    cluster_halond_start
    [ $? -eq 1 ] && return 1
    echo "Starting EOS cluster now"
    $pdsh_RC_host $timeout_cmd $timeout hctl mero start
    [ $? -ne 0 ] && return 1
    echo "Waiting for cluster services to come onlne"
    sleep 1m
    echo "Checking EOS cluster status"
    $pdsh_RC_host $timeout_cmd $timeout hctl mero status
    [ $? -ne 0 ] && return 1
    echo "If some services are marked as failed or inhibited," \
        "check logs in 'journalctl -xe' to know the details"
    return 0
}

cluster_eos_start()
{
    yesopt=$1
    # Check cluster status
    echo "----- Checking cluster status..-----"
    [ -d /var/lib/halon/halon-persistence/replicas ] || {
        echo "No halon persistent data found at /var/lib/halon"
        echo "Eos is not configured, to configure it again"\
            "run config/config.sh script to setup everything" \
            "scratch or run utils/cluster-bootstrap.sh -y to" \
            "bootstrap the cluster with existing configuration."
        exit 0
    }
    cluster_status_get
    ret=$?
    case $? in
        0)
            echo "EOS Cluster is already started"
            return 0
            ;;
        1)
            echo "EOS Cluster is offline, starting.."
            cluster_mero_start
            return $?
            ;;
        2)
            #CLuster is in failed state.
            #Take corrective action.
            #Stop the cluster, restart the
            #services & start the cluster again.

            # Check if mero kernel module failed to start
            grep "mero-kernel failed to start" $cs_tmpfile
            if [ $? -eq 0 ]; then
                cluster_lnet_dignose_and_fix || return 1
            fi
            echo "Stopping the cluster"
            cluster_stop $yesopt
            echo "Restarting the cluster again"
            cluster_mero_start
            cluster_status_get
            [ $? -ne 0 ] && echo "Could not restart the cluster" && return 1

            echo "Cluster started successfully"
            return 0
            ;;
        3)
            # hctl mero status is hung
            # TODO: Check if halon conf file has correct netif.
            cluster_lnet_dignose_and_fix || return 1
            systemctl stop halond
            cluster_mero_start
            cluster_status_get
            [ $? -ne 0 ] && echo "Could not restart the cluster" && return 1
            ;;
        *)
            echo "Invalid return code from cluster_status_get()"
            ;;
    esac
}

s3server_config_restore()
{
    echo "---- Restoring s3 server congifuration date ----"
    echo "****************** WARNING *********************"
    echo "* This is required only if s3server package is *"
    echo "* reinstalled and the configuration data of the*"
    echo "* previous install is to be restored.          *"
    echo "************************************************"
    ask_yes_no_skip "Skip this step if you have not re-installed the s3server package"
    if [ $?  -eq 0 ]; then
        $pdsh_client_hosts cp -f /tmp/kd/15oct/s3config.yaml /opt/seagate/s3/conf/s3config.yaml
        $pdsh_client_hosts cp -f /tmp/kd/15oct/auth_resources/*.* /opt/seagate/auth/resources/
        $pdsh_client_hosts systemctl restart s3authserver
        $pdsh_client_hosts systemctl status s3authserver -l | grep -i active
        $pdsh_client_hosts netstat -anp | grep 9086
        echo "done.."
        return 0
    fi
    echo "Skipping the step to restore old s3config"
}

cluster_add_client_nodes()
{
    ask_yes_no_skip "---- Adding clients to the cluster ----"
    if [ $?  -eq 0 ]; then
        $pdsh_client_hosts halonctl halon node add -t $RC_halon_port
    fi
}

cluster_enable_stats()
{
    local yn=$1
    local s3config="/opt/seagate/s3/conf/s3config.yaml"
    echo "----------------Enabling stats ----------------"
    echo "This is for tuning s3 server performance."
    ask_yes_no_skip $yn "Skip if you want to keep default values."
    if [ $?  -eq 0 ]; then
        echo "Enabling S3 stats.."
        $pdsh_client_hosts sed -i 's/S3_ENABLE_STATS:  *false/S3_ENABLE_STATS: true/g' $s3config
        echo "Setting S3 log mode to INFO.."
        $pdsh_client_hosts sed -i 's/S3_LOG_MODE: *DEBUG/S3_LOG_MODE: INFO/g' $s3config
        echo "Disabling S3 Log buffering.."
        $pdsh_client_hosts sed -i 's/S3_LOG_ENABLE_BUFFERING: *false/S3_LOG_ENABLE_BUFFERING: true/g' $s3config
        echo -e "Setting S3 Max Units/Request to 8..\n"
        $pdsh_client_hosts sed -i 's/S3_CLOVIS_MAX_UNITS_PER_REQUEST: *1/S3_CLOVIS_MAX_UNITS_PER_REQUEST: 8/g' $s3config
    fi
}
