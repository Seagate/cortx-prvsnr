#!/bin/bash

script_dir=$(dirname $0)
source $script_dir/eos-ops.sh

mero_rpm=
halon_rpm=
s3server_rpm=
sspl_rpm=()
mero_pkg=
s3server_pkg=
halon_pkg=
sspl_pkg=()

if [ $use_stx_prvsnr = "yes" ]; then
    yum_server="stx-prvsnr.mero.colo.seagate.com"
    pdsh_yum_server="$pdsh_cmd $yum_server"
    releases="/ci-storage/releases/hermi"
    repo_dir="/prvsnr/vendor/hermi/Packages"
    FILE=`$pdsh_yum_server ls -lrt $releases | grep last_successful | \
         awk '{ print $12 }'`
    build=`basename "$FILE"`
    build_dir="$releases/$build"
else
    echo "Error: use_stx_prvsnr is set to no"
    echo "Please set use_stx_prvsnr =\"yes\" in" \
        "$script_dir/cluster-defs.sh and rerun the command."
    exit 1
fi

update_repo()
{
    local rpm_file=$2
    $pdsh_yum_server test -e $rpm_file
    if [ $? -ne 0 ]; then
        echo "rrm file doesn't exists: $rpm_file"
        return 1
    fi
    echo -e "\n---- Copying following latest $1 rpm to $repo_dir ----"
    echo "$rpm_file"
    while true; do
        read -p "Proceed? [y/n]" proceed
        case $proceed in
            [Yy]* ) $pdsh_yum_server cp $rpm_file $repo_dir;
                    echo "copied $rpm_file to $repo_dir";
                    return 0;;
            [Nn]* ) echo "Skipping $1"; return 0;;
            * ) echo "Please answer y or n";;
        esac
    done
}

update_repo_sspl()
{
    declare -a rpm_loc=("$build_dir/sspl/repo/sspl-1.0.1*.rpm"
                        "$build_dir/sspl/repo/libsspl_sec-1.0.1*.rpm"
                        "$build_dir/sspl/repo/libsspl_sec-devel-1.0.1*.rpm"
                        "$build_dir/sspl/repo/libsspl_sec-method_none*.rpm"
                        "$build_dir/sspl/repo/libsspl_sec-method_pki-1.0.1*.rpm"
                        )
    local j=0
    for i in "${rpm_loc[@]}"
    do
        ssplrpm="$($pdsh_yum_server ls $i | awk '{ print $2 }')"
        sspl_rpm[$j]=`basename "$ssplrpm"`
        sspl_pkg[$j]="`echo $sspl_rpm | rev | cut -f 2- -d '.' | rev`"
        update_repo sspl $ssplrpm
        j=$(( $j + 1 ))
    done
}

update_repo_mero()
{
    local rpm_loc="$build_dir/mero/repo/mero-1.4.0*.rpm"
    local mrpm="$($pdsh_yum_server ls $rpm_loc | awk '{ print $2 }')"
    mero_rpm=`basename "$mrpm"`
    mero_pkg=`echo $mero_rpm | rev | cut -f 2- -d '.' | rev`
    update_repo mero $mrpm
}

update_repo_halon()
{
    local rpm_loc="$build_dir/halon/repo/halon-1.2*.rpm"
    local hrpm="$($pdsh_yum_server ls $rpm_loc | awk '{ print $2 }')"
    halon_rpm=`basename "$hrpm"`
    halon_pkg=`echo $halon_rpm | rev | cut -f 2- -d '.' | rev`
    update_repo halon $hrpm
}

update_repo_s3server()
{
    #TODO: Also install s3iamcli
    local rpm_loc="$build_dir/s3server/repo/s3server-1.0*.rpm"
    local s3rpm="$($pdsh_yum_server ls $rpm_loc | awk '{ print $2 }')"
    s3server_rpm=`basename "$s3rpm"`
    s3server_pkg=`echo $s3server_rpm | rev | cut -f 2- -d '.' | rev`
    update_repo s3server $s3rpm
}

clean_yum_cache_all_nodes()
{
    echo -e "\n---- Cleaning yum cache on all ssu and client nodes ----"
    $pdsh_all_nodes yum clean all; rm -rf /var/cache/yum
}

create_yum_repo()
{
    echo "---------------------------Listing copied rpms---------------------------"
    echo "$repo_dir:"
    $pdsh_yum_server ls -lt $repo_dir | grep -E "$mero_rpm|$halon_rpm|$s3server_rpm"
    for i in "${sspl_rpm[@]}"
    do
        $pdsh_yum_server ls -lt $repo_dir | grep $i
    done
    echo "-------------------------------------------------------------------------"

    ask_yes_no_skip "---- Creating yum repo with the latest rpms ----"
    if [ $? -eq 0 ];then
        $pdsh_yum_server /usr/bin/createrepo $repo_dir/../ 
        clean_yum_cache_all_nodes
    fi
}

remove_existing_packages()
{
    ask_yes_no_skip "---- Before removing the packages, cluster needs to be stopped ----"
    ret=$?
    if [ $ret -eq 0 ]; then
        cluster_stop_and_cleanup
    fi
    ask_yes_no_skip "---- Removing existing mero, halon & s3server packages ----"
    ret=$?
    if [ $ret -eq 0 ]; then
        #TODO: Add sspl packages
        $pdsh_client_hosts yum remove -y s3server
        $pdsh_all_nodes yum remove -y halon
        $pdsh_all_nodes yum remove -y mero
        return 0
    fi
    echo "Not removing packages"; return 1
}

install_new_packages()
{
    echo -e "\n---- hermi repo at stx-prvsnr:$FILE ----"
    ask_yes_no_skip "---- Installing mero, halon & s3server packages ----"
    ret=$?
    if [ $? -eq 0 ]; then
        # mero package will be installed as part of halon dependency.
        for spkg in "${sspl_pkg[@]}"
        do
            $pdsh_all_nodes yum install -y $spkg
        done
        $pdsh_all_nodes yum install -y $halon_pkg
        $pdsh_client_hosts yum install -y $s3server_pkg
        return 0
    else
        echo "Not installing packages"; return 1
    fi
}

main()
{
    print_warning
    echo ""
    echo "-------------------------------------------------------------------"
    echo "This script is intended to be run from cmu."
    echo "This will erase the mero, halon packages on ssu and s3server nodes."
    echo "The cluster will be stopped during the process and after installing"
    echo "packages the cluster will be bootstrapped again, this will result in "
    echo "loss the data written on the object storage."
    echo "-------------------------------------------------------------------"
    ask_yes_no "Proceed wisely"
    if [ $? -eq 0 ]; then
        echo "Proceeding"
    fi
    update_repo_sspl
    update_repo_mero
    update_repo_halon
    update_repo_s3server
    create_yum_repo
    remove_existing_packages
    install_new_packages
    cluster_enable_stats
    ask_yes_no_skip "---- Bootstrapping the cluster now..----"
    if [ $? -eq 0 ]; then
        cluster_bootstrap
    fi
}

main
