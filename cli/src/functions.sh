#!/bin/bash

cli_scripts_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# rpm package places scripts in parent folder
if [[ "$(basename $cli_scripts_dir)" == 'cli' ]]; then
    repo_root_dir="$(realpath $cli_scripts_dir/../)"
else
    repo_root_dir="$(realpath $cli_scripts_dir/../../)"
fi


# TODO API for error exit that might:
#       - echos to stderr
#       - print usage (optionally)
#       - exits with specified code

# general set of arguments
# TODO should be added to docs as part of the API
dry_run=false
hostspec=
singlenode=false
ssh_config=
sudo=false
verbosity=0


base_options_usage="\
  -h,  --help                     print this help and exit
  -r,  --remote [user@]hostname   remote host specification
  -S,  --singlenode               switch to single node mode setup
  -F,  --ssh-config FILE          alternative path to ssh configuration file
  -v,  --verbose                  be more verbose
"
# disabled options (EOS-2410)
#  -n,  --dry-run                  do not actually perform any changes
#  -s,  --sudo                     use sudo

# default usage
# TODO mention in docs how to override
function usage {
  echo "\
Usage: $0 [options]

Options:
$base_options_usage
"
}


#   log level message
#
#   Logs a message if its log level satisifies current current verbosity:
#       trace: >= 2
#       debug: >= 1
#       info: >= 0
#       warning: >= 0
#       error: >= 0
#
#   Thus erros, warnings and info messages are always logged.
#   Note. errors and warnings are logged to stderr.
#
#   Args:
#       level: a string that specifies logging level,
#           possible options: trace, debug, info, warn, error
#       message: a message to log
#
function log {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _level=$1
    local _message=$2

    local _verbosity=-1
    local _error=false

    case "$_level" in
        trace)
            _verbosity=2
            ;;
        debug)
            _verbosity=1
            ;;
        info)
            _verbosity=0
            ;;
        warn)
            _verbosity=0
            _error=true
            _level=warning
            ;;
        error)
            _verbosity=0
            _error=true
            ;;
        *)
            l_error "Unknown log level: $_level"
            exit 5
    esac


    if [[ "$verbosity" -ge "$_verbosity" ]]; then
        _level=$(echo "$_level" | tr '[:lower:]' '[:upper:]')
        _message="$_level: $_message"

        if [[ "$_error" == true ]]; then
            >&2 echo "$_message"
        else
            echo "$_message"
        fi
    fi
}

#   l_* message
#
#   Log helpers for a handy logging.
#
#   Args:
#       message: a message to log
#
function l_trace {
    log trace "$1"
}

function l_debug {
    log debug "$1"
}

function l_info {
    log info "$1"
}

function l_warn {
    log warn "$1"
}

function l_error {
    log error "$1"
}


#   parse_args <add_opts_short> <add_opts_long> <add_opts_parse_cb> <positional_args_cb> <options_to_parse>
#
#   Uses `getopt` (`man 1 getopt`) to parse short and long options.
#
#   Holds a predefined set of general options: `check base_options_usage` variable.
#
#   Provides an API to extend that options list:
#       1. additional short options might be passed as non-blank `add_opts_short`
#       2. additional long options might be passed as non-blank `add_opts_long`
#       3. if additional options are expected non-blank `add_opts_parse_cb` must be specified
#       4. if positional arguments are expected `positional_args_cb` must be specified
#
#   All these arguments are required (either blank or non-blank).
#   All other arguments are treated as original command line string to parse and usually
#   it would be: `"$@"`.
#
#   Args:
#       add_opts_short: a string of one-letter additional options.
#       add_opts_long: a comma-separated string of long additional options.
#       add_opts_parse_cb: a function name to call to parse additional options.
#           In case of an error must exits with some error code.
#           No calls of `shift` is required.
#       positional_args_cb: a function name to call to parse positional arguments.
#
#   Returns:
#       In case of success returns 0 and the following global variables are assigned:
#           - dry_run
#           - hostspec
#           - singlenode
#           - ssh_config
#           - sudo
#           - verbosity
#
#       Otherwise exits with the following codes:
#           - 0: success
#           - 1: getopt can't be used in the environment (self getopt's test fails)
#           - 2: command line arguments don't satisfy the specification
#               (e.g. unknown option or missed required argument)
#           - 3: some other getopt error
#           - 4: options parser callback is not defined when it is expected
#           - 5: bad argument values (e.g. not a file for ssh-config)
#
#   Examples:
#
#       1. parse only general set of options with no paositional arguments expected
#
#           `parse_args '' '' '' '' "$@`
#
#       2. parse additional options

#            add_opt1_value=
#            add_opt2_value=
#
#            function options_parser {
#                set -eu
#                case "$1" in
#                    -a|--add-option1)
#                        add_opt1_value=true
#                        ;;
#                    -A|--add-option2)
#                        add_opt2_value="$2"
#                        ;;
#                    *)
#                        l_error "Unknown option: $1"
#                        exit 5
#                esac
#            }
#
#           `parse_args 'aA:' 'add-option1,add-option2:' 'options_parser' '' "$@`
#
#       3. parse positional arguments
#
#            pos_arg=
#
#            function pos_args_parser {
#                set -eu
#                if [[ $# -gt 1 ]]; then
#                    l_error "$0: Only one positional argument is expected, provided: $@"
#                    exit 2
#                fi
#
#                pos_arg="${1:-}"
#            }
#
#           `parse_args '' '' '' 'pos_args_parser' "$@`
#
function parse_args {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _add_opts=$1
    local _add_long_opts=$2
    local _opts_cb=$3
    local _positional_args_cb=$4
    local _res
    shift 4

    ! getopt --test > /dev/null
    if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
        l_error 'Error: getopt is not functional.'
        exit 1
    fi

    local _opts=nhr:SF:sv
    if [[ -n $_add_opts ]]; then
        _opts=$_opts$_add_opts
    fi

    local _long_opts=dry-run,help,remote:,singlenode,ssh-config:,sudo,verbose
    if [[ -n $_add_long_opts ]]; then
        _long_opts=$_long_opts,$_add_long_opts
    fi

    local _getopt_res
    ! _getopt_res=$(getopt --name "$0" --options=$_opts --longoptions=$_long_opts -- "$@")
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        exit 2
    fi

    # TODO why eval here
    eval set -- "$_getopt_res"

    while true; do
        case "$1" in
            -n|--dry-run)
                # disabled EOS-2410
                # dry_run=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -r|--remote)
                hostspec="$2"
                shift 2
                ;;
            -S|--singlenode)
                singlenode=true
                shift
                ;;
            -F|--ssh-config)
                ssh_config="$2"
                if [[ ! -f "$ssh_config" ]]; then
                    l_error "'$ssh_config' not a file"
                    exit 5
                fi
                shift 2
                ;;
            -s|--sudo)
                # disabled EOS-2410
                # sudo=true
                shift
                ;;
            -v|--verbose)
                ((verbosity=verbosity+1))
                shift
                ;;
            --)
                shift
                break
                ;;
            ?)
                l_error "Runtime error"
                exit 3
                ;;
            *)
                if [[ -z "$_opts_cb" ]]; then
                    l_error "Options parser callback is not defined"
                    exit 4
                fi

                $_opts_cb "$@"

                local _opt=$(echo "$1" | sed 's/^-\+//g')
                if (echo "$_add_opts" | grep -qP "$_opt(?=:)") || (echo ",$_add_long_opts" | grep -qP ",$_opt(?=:)"); then
                    shift 2
                else
                    shift
                fi
                ;;
        esac
    done

    if [[ -n "$_positional_args_cb" ]]; then
        $_positional_args_cb "$@"
    elif [[ $# -gt 0 ]]; then
        l_error "$0: positional arguments are not expected, provided: $@"
        exit 2
    fi

    local _res="dry-run=<$dry_run>, remote=<$hostspec>"
    _res+=", singlenode=<$singlenode>, ssh-config=<$ssh_config>"
    _res+=", sudo=<$sudo>, verbosity=<$verbosity>"
    l_debug "Parsed common args: $_res"
}


#   build_command [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Constructs command as a prefix for other commands to run over ssh and/or
#   with sudo usage and echoes the result into stdout.
#
#   If no arguments provided will return just an empty string.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
#   Outputs:
#       Prepared `ssh` command if `hostspec` is specified. `sudo` would be added at the end
#       if it was required.
#
function build_command() {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"

    local _cmd=''
    if [[ -n "$_hostspec" ]]; then
        _cmd='ssh'

        if [[ "$_sudo" == true ]]; then
            _cmd="$_cmd -t"
        fi

        if [[ -n "$_ssh_config" ]]; then
            _cmd="$_cmd -F $_ssh_config"
        fi

        _cmd="$_cmd $_hostspec"
    fi

    if [[ "$_sudo" == true ]]; then
        _cmd="$_cmd sudo"
    fi

    echo $_cmd
}


#   hostname_from_spec <hostspec>
#
#   Extracts and echoes hostname of the hostspec into stdout.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#
#   Outputs:
#       An extracted hostname value.
#
function hostname_from_spec {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _hostname="$1"
    if [[ $_hostname == *"@"* ]]; then
        IFS='@' read -a _arr <<< $_hostname
        if [[ "${#_arr[@]}" -eq 2 ]]; then
            _hostname="${_arr[1]}"
        else
            _hostname=
        fi
    fi
    echo "$_hostname"
}


#   check_host_in_ssh_config <hostspec> <ssh-config>
#
#   Checks a hostname part of the specified hostspec in provided ssh config file
#   and returns matched string if found.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#       ssh-config: past to an alternative ssh-config file.
#
#   Outputs:
#       Matched string from the ssh-config file which starts the hostname
#       ssh config specification block.
#
function check_host_in_ssh_config {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _hostspec=$1
    local _ssh_config=$2

    local _hostname="$(hostname_from_spec "$_hostspec" 2>/dev/null)"

    if [[ -f "$_ssh_config" && -n "$_hostname" ]]; then
        echo "$(grep "^Host[[:space:]]\+$_hostname" "$_ssh_config")"
    fi
}


#   TODO
#       - yum limits to centos/redhat for now

#   collect_addrs [<hostspec> [<ssh-config>]]
#
#   Collects addresses / domain names either for the local or remote host.
#   Tries to use tools like ifconfig, ip, hostname ...
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
function collect_addrs {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" 2>/dev/null)"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    yum -y install iproute >&2

    ip_list="\$(ip addr show scope global up | sed -n "s/.*inet \([^/]\+\).*/\1/p" || true)"
    ifconfig_list="\$(ifconfig 2>/dev/null | sed -n "s/.*inet \([^ ]\+\).*/\1/p" | grep -v 127.0.0.1 || true)"
    hostname="\$(hostname | grep -v 127.0.0.1 || true)"
    echo \$ip_list \$ifconfig_list \$hostname | awk "{for(i = 1; i<=NF; i++) {print \\\$i}}" | sort -u | paste -sd " " -
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}


#   check_host_reachable <destination> [<hostspec> [<ssh-config>]]
#
#   Check whether destination host is reachable either
#   from the remote host or locally.
#
#   Args:
#       destination: either IP or domain of the host to check
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
function check_host_reachable {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _dest="$1"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" 2>/dev/null)"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    ping -c 1 -W 1 $_dest
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    ! $_cmd bash -c "$_script" >/dev/null 2>&1

    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        echo -n "$_dest"
    fi
}



#   get_reachable_host_names <hostspec1> <ssh-config> [<hostspec2>]
#
#   Collect names of the host specified by `hostspec1` reachable from
#   the another host specified by `hostspec2`.
#
#   Args:
#       hostspec1: either IP or domain of the destination host
#       hostspec2: either IP or domain of the source host
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
function get_reachable_host_names {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _hostspec1="${1:-}"
    local _hostspec2="${2:-}"
    local _ssh_config="${3:-}"

    local _res=()

    if [[ "$_hostspec1" == "$_hostspec2" ]]; then
        l_error "host1 and host2 can't be the same, provided: $_hostspec1"
        exit 1
    fi

    _host1_addrs="$(collect_addrs "$_hostspec1" "$_ssh_config")"
    _host2_addrs="$(collect_addrs "$_hostspec2" "$_ssh_config")"

    for _addr in $_host1_addrs; do
        if [[ "$_host2_addrs" == *"$_addr"* ]]; then
            l_warn "ignoring common host name: $_addr"
        else
            if [[ -n "$(check_host_reachable "$_addr" "$_hostspec2" "$_ssh_config" 2>/dev/null)" ]]; then
                _res+=("$_addr")
                break
            fi
        fi
    done

    echo "${_res[*]}"
}


#   install_repos [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Install package repositories either on the remote host or locally.
#   The function assumes that '../../files/etc/yum.repos.d' exists.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
function install_repos {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    local _repo_base_dir="/etc/yum.repos.d"
    local _repo_base_dir_backup="/etc/yum.repos.d.bak"
    local _project_repos="$repo_root_dir/files/etc/yum.repos.d"

    l_info "Installing replacing package repositories '$_hostspec'"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # config custom repos
    yum clean expire-cache
    rm -rf /var/cache/yum

    if [[ -d "$_repo_base_dir" && ! -d "$_repo_base_dir_backup" ]]; then
        cp -R "$_repo_base_dir" "$_repo_base_dir_backup"
    else
        echo -e "\\nWARNING: skip backup creation since backup already exists" >&2
    fi

    rm -rf "$_repo_base_dir"

    # TODO a temporary fix since later version (2019.2.1) is buggy
    # (https://repo.saltstack.com/#rhel, instructions for minor releases centos7 py3)
    rpm --import https://repo.saltstack.com/py3/redhat/7/x86_64/archive/2019.2.0/SALTSTACK-GPG-KEY.pub

    if [[ -z "$_hostspec" ]]; then
        cp -R "$_project_repos" "$_repo_base_dir"
    fi
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"

    if [[ -n "$_hostspec" ]]; then
        scp -r -F "$_ssh_config" "$_project_repos" "${_hostspec}":"$_repo_base_dir"
    fi
}

#   configure_firewall [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Open firewall ports for saltstack either on the remote host or locally.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
function configure_firewall {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Configuring firewall ports for saltstack '$_hostspec'"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    #Disable iptables-services
    systemctl stop iptables && systemctl disable iptables && systemctl mask iptables
    systemctl stop iptables6 && systemctl disable iptables6 && systemctl mask iptables6
    systemctl stop ebtables && systemctl disable ebtables && systemctl mask ebtables

    #Install and start firewalld
    yum install -y firewalld
    systemctl start firewalld
    systemctl enable firewalld

    # Open salt firewall ports
    firewall-cmd --zone=public --add-port=4505-4506/tcp --permanent
    firewall-cmd --reload

EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}

#   install_sg3_utils [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Install sg3_utils either on the remote host or locally.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
function install_sg3_utils {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Installing sg3_utils on '$_hostspec'"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # Install sg3_util and rescan iSCSI devices.
    yum install sg3_utils -y
    rescan-scsi-bus.sh
    
EOF
    # TODO install salt-ssh salt-syndic as well as eos-prvsnr rpm supposes

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}

#   configure_multipath [<minion-ids> [<hostspec> [<ssh-config> [<sudo>]]]]
#
#   Install and configure multipath either on the remote host or locally.
#
#   Args:
#       minion-ids: a space separated list minion ids which keys should be accepted.
#           Default: `eosnode-1`.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
function configure_multipath {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _minion_id="$1"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"
    local _master="${5:-true}"

    local _multipath_config_file="/etc/multipath.conf"
    local _multipath_config_repo_file="$repo_root_dir/files/etc/multipath.conf"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Installing and Configuring multipath '$_minion_id'"

    if [[ $($_cmd rpm -qa salt-master) ]]; then
        $_cmd salt -t $_timeout "$_minion_id" state.apply components.system.storage.multipath
    fi

    l_info  "Installing and Configuring multipath on $_minion_id complete."
}

#   install_salt [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Install SaltStack either on the remote host or locally.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
function install_salt {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Installing salt on '$_hostspec'"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # Remove any older saltstack if any.
    systemctl stop salt-minion salt-master || true
    yum remove -y salt-minion salt-master

    # install salt master/minion
    yum install -y salt-minion salt-master
EOF
    # TODO install salt-ssh salt-syndic as well as eos-prvsnr rpm supposes

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}


#   install_provisioner [<repo-src> [<prvsnr-version> [<hostspec> [<ssh-config> [<sudo> [<singlenode> [<installation-dir>]]]]]]]
#
#   Install provisioner repository either on the remote host or locally using
#   one of possible types of sources.
#
#   Prerequisites:
#       - (for rpm only) SaltStack is available.
#
#   Args:
#       repo-src: One of the following:
#           `rpm` - installs from a rpm package (default),
#           `gitlab` - installs from GitLab using the specified
#               version `prvsnr-version`. If the version is not set
#               uses the latest tagged one.
#           `gitrepo` - establishes local git repo at `/opt/seagate/eos-prvsnr`
#               pointing to remote repo on GitLab. This should help use switch between
#               branches for validation of branched changes.
#           `local` - copies local working copy of the repository, assumes
#               that script is a part of it.
#       prvsnr-version: The version of the EOS provisioner to install. Makes sense only
#           for `gitlab` source for now. Default: not set.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       singlenode: a flag for a singlenode setup mode. Expected values: `true` or `false`.
#           Default: `false`
#       installation-dir: destination installation directory.
#           Default: /opt/seagate/eos-prvsnr
#
function install_provisioner {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _repo_src="${1:-rpm}"
    local _prvsnr_version="${2:-}"
    local _hostspec="${3:-}"
    local _ssh_config="${4:-}"
    local _sudo="${5:-false}"
    local _singlenode="${6:-false}"
    local _installdir="${7:-/opt/seagate/eos-prvsnr}"
    local _os_release="centos-7.7.1908"

    local _prvsnr_repo=
    local _repo_archive_path=
    local _tmp_dir=$(mktemp -d)

    local _cluster_sls_src
    if [[ "$_singlenode" == true ]]; then
        _cluster_sls_src="$_installdir/pillar/components/samples/singlenode.cluster.sls"
    else
        _cluster_sls_src="$_installdir/pillar/components/samples/ees.cluster.sls"
    fi

    l_info "Installing repo on '$_hostspec' into $_installdir with $_repo_src as a source (version is $_prvsnr_version), singlenode is $_singlenode"

    # assuming that 'local' mode would be used only in dev setup within the repo
    if [[ "$_repo_src" == "local" ]]; then
        # might not always work
        local _repo_archive_name='repo.tgz'
        local _scp_opts=
        _repo_archive_path="$_tmp_dir/$_repo_archive_name"

        pushd "$repo_root_dir"
            if [[ -n "$_prvsnr_version" ]]; then  # treat the version as git commit/branch/tag ...
                git archive --format=tar.gz "$_prvsnr_version" -o "$_repo_archive_path"
            else  # do raw archive with uncommitted/untracked changes otherwise
                tar -zcf "$_repo_archive_path" \
                    --exclude=".build" \
                    --exclude="build" \
                    --exclude=".boxes" \
                    --exclude=".eggs" \
                    --exclude=".vdisks" \
                    --exclude=".vagrant" \
                    --exclude=".pytest_cache" \
                    --exclude="__pycache__" \
                    --exclude="packer_cache" \
                    --exclude="tmp" \
                    -C "$repo_root_dir" .
            fi

            if [[ -n "$_hostspec" ]]; then
                if [[ -n "$_ssh_config" ]]; then
                    _scp_opts="-F $_ssh_config"
                fi

                $(scp $_scp_opts $_repo_archive_path ${_hostspec}:/tmp)
                rm -rfv "$_tmp_dir"
                _repo_archive_path="/tmp/$_repo_archive_name"
            fi
        popd
    elif [[ "$_repo_src" == "rpm" ]]; then
        if [[ -z "$_prvsnr_version" ]]; then
            _prvsnr_version="integration/$_os_release/last_successful"
        fi
    fi

! read -r -d '' _prvsnr_repo << EOF
[provisioner]
gpgcheck=0
enabled=1
baseurl=http://ci-storage.mero.colo.seagate.com/releases/eos/$_prvsnr_version
name=provisioner
EOF

    if [[ "$_repo_src" != "gitlab" && "$_repo_src" != "rpm" && "$_repo_src" != "local" && "$_repo_src" != "gitrepo" ]]; then
        l_error "unsupported repo src: $_repo_src"
        exit 1
    fi

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

if [[ "$_repo_src" == "gitrepo" ]]; then
    if ! grep gitlab ~/.ssh/config 1>/dev/null ; then 
! read -r -d '' GITLAB <<- EOM
    Host gitlab.mero.colo.seagate.com
        User root
        UserKnownHostsFile /dev/null
        StrictHostKeyChecking no
        IdentityFile /root/.ssh/id_rsa_prvsnr
        IdentitiesOnly yes
EOM
        echo $GITLAB >> ~/.ssh/config
    fi
fi

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # TODO test cases when installation dir is presented and not empty
    # issue #23
    #rm -rvf "$_installdir"
    mkdir -p "$_installdir"
    if [[ "$_repo_src" == "gitlab" ]]; then
        pushd "$_installdir"
            curl "http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr/-/archive/${_prvsnr_version}/${_prvsnr_version}.tar.gz" | tar xzf - --strip-components=1
        popd
    elif [[ "$_repo_src" == "gitrepo" ]]; then
        pushd "$_installdir"
            yum install -y git
            git init
            if ! git remote show origin >/dev/null 2>&1 ; then
                git remote add origin http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr.git
            else
                git remote set-url origin http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr.git
            fi
            git fetch origin
            git checkout -B ${_prvsnr_version} origin/${_prvsnr_version} -f
            # git clean -fdx        # Commented because there could be intentional changes in workspace.
        popd
    elif [[ "$_repo_src" == "rpm" ]]; then
        echo "$_prvsnr_repo" >/etc/yum.repos.d/prvsnr.repo
        yum install -y eos-prvsnr
    else
        # local
        tar -zxf "$_repo_archive_path" -C "$_installdir"
        rm -vf "$_repo_archive_path"
    fi
    cp -f "$_cluster_sls_src" "$_installdir/pillar/components/cluster.sls"
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}


# TODO better to have similar logic as part of salt formulas
#
#   configure_network [<hostspec> [<ssh-config> [<sudo> [<installation-dir>]]]]
#
#   Configures network on the EOS stack node either on local or remote host.
#
#   Prerequisites:
#       - The provisioner repo is installed.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       installation-dir: destination installation directory.
#           Default: /opt/seagate/eos-prvsnr
#
function configure_network {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"
    local _installdir="${5:-/opt/seagate/eos-prvsnr}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Configuring network on '$_hostspec'"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    pushd "$_installdir"
        if [[ -n "\$(rpm -qi NetworkManager | grep "^Version" 2>/dev/null)" ]]; then
          systemctl stop NetworkManager
          systemctl disable NetworkManager
          yum remove -y NetworkManager
        fi

        mkdir -p /etc/sysconfig/network-scripts/
        cp -f files/etc/sysconfig/network-scripts/ifcfg-* /etc/sysconfig/network-scripts/
        cp -f files/etc/modprobe.d/bonding.conf /etc/modprobe.d/bonding.conf
    popd
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}


#   configure_salt <minion-id> [<hostspec> [<ssh-config> [<sudo> [<is-master> [<master-host> [<installation-dir>]]]]]]
#
#   Configures salt minion (ans salt master if `is-master` set to `true`) either on the local or remote host.
#
#   Prerequisites:
#       - SaltStack is installed.
#       - The provisioner repo is installed.
#
#   Args:
#       minion-id: an id of the minion.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       is-master: A flag to switch between primary / secondary EOS stack nodes.
#           Default: `true`.
#       master-host: A resolvable (from within the minion's host) domain name or IP of the salt master.
#           Default: not set.
#       installation-dir: destination installation directory.
#           Default: /opt/seagate/eos-prvsnr
#
function configure_salt {
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    local _script

    local _minion_id="$1"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"
    local _master="${5:-true}"
    local _master_host="${6:-}"
    local _installdir="${7:-/opt/seagate/eos-prvsnr}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Configuring salt on '$_hostspec': minion-id $_minion_id, is-master $_master, master host $_master_host"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    pushd "$_installdir"
        # re-config salt master
        if [[ ! -f /etc/salt/master.org ]]; then
            mv -f /etc/salt/master /etc/salt/master.org
            cp files/etc/salt/master /etc/salt/master
        fi

        if [[ "$_master" == true ]]; then
            systemctl enable salt-master
            systemctl restart salt-master
        fi

        # re-config salt minion
        if [[ ! -f /etc/salt/minion.org ]]; then
            mv -f /etc/salt/minion /etc/salt/minion.org
            cp files/etc/salt/minion /etc/salt/minion
        fi

        if [[ -n "$_master_host" ]]; then
            sed -i "s/^master: .*/master: $_master_host/g" /etc/salt/minion
        fi

        if [[ "$_master" == true ]]; then
            cp -f files/etc/salt/grains.primary /etc/salt/grains
        else
            cp -f files/etc/salt/grains.slave /etc/salt/grains
        fi

        echo "$_minion_id" >/etc/salt/minion_id

        systemctl enable salt-minion
        systemctl restart salt-minion
    popd
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}


#   accept_salt_keys [<minion-ids> [<hostspec> [<ssh-config> [<sudo> [<timeout>]]]]]
#
#   Makes keys for the specified list of minions accepted by the salt master.
#
#   Salt master might be either local or remote host.
#
#   Prerequisites:
#       - SaltStack is installed.
#       - The provisioner repo is installed.
#       - EOS stack salt master/minions are configured.
#
#   Args:
#       minion-ids: a space separated list minion ids which keys should be accepted.
#           Default: `eosnode-1`.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       timeout: a time to wait until a minion becomes connected to master.
#           Default: `false`.
#
function accept_salt_key {
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    local _script

    local _id="${1:-eosnode-1}"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"
    local _timeout="${5:-30}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Accepting minion id $_id on salt master '$_hostspec', timeout $_timeout"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    try=1
    echo -e "\\nINFO: waiting for minion $_id to become connected to master"
    until salt-key --list-all | grep $_id >/dev/null 2>&1
    do
        if [[ "\$try" -gt "$_timeout" ]]; then
            echo -e "\\nERROR: minion $_id seems not connected after $_timeout seconds." >&2
            salt-key --list-all >&2
            exit 1
        fi
        echo -n "."
        try=\$(( \$try + 1 ))
        sleep 1
    done
    echo -e "\\nINFO: Key $_id is connected."

    # minion is connected but does not need acceptance
    if [[ -z "\$(salt-key --list unaccepted | grep $_id 2>/dev/null)" ]]; then
        echo -e "\\nINFO: no key acceptance is needed for minion $_id." >&2
        salt-key --list-all >&2
        exit 0
    fi

    salt-key -y -a $_id

    if [[ -z "\$(salt-key --list accepted | grep $_id 2>/dev/null)" ]]; then
        echo -e "\\nINFO: Key $_id is accepted." >&2
        exit 0
    fi
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}


#   eos_pillar_show_skeleton <component> [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Calls `configure-eos.py` util either locally or remotely to dump a skeleton
#   of the configuration yaml for the specified `component`.
#
#   Prerequisites:
#       - The provisioner repo is installed.
#
#   Args:
#       component: a name of the provisioner repo component.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       timeout: a time to wait until a minion becomes connected to master.
#           Default: `false`.
#
function eos_pillar_show_skeleton {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _component="$1"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    # TODO is it ok that we stick to python3.6 here ?
    $_cmd python3.6 /opt/seagate/eos-prvsnr/cli/utils/configure-eos.py ${_component} --show-${_component}-file-format
}


#   eos_pillar_update <component> <file-path> [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Calls `configure-eos.py` util either locally or remotely to update
#   the configuration yaml for the specified `component` using `file-path`
#   as a source.
#
#   Prerequisites:
#       - The provisioner repo is installed.
#
#   Args:
#       component: a name of the provisioner repo component.
#       file-path: remote host specification in the format [user@]hostname.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
function eos_pillar_update {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _component="$1"
    local _file_path="$2"
    local _hostspec="${3:-}"
    local _ssh_config="${4:-}"
    local _sudo="${5:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Updating a pillar component $_component on '$_hostspec' using $_file_path as a source"

    # TODO test
    if [[ ! -f "$_file_path" ]]; then
        l_error "not a file: $_file_path"
        exit 1
    fi

    if [[ -n "$_hostspec" ]]; then
        if [[ -n "$_ssh_config" ]]; then
            _ssh_config="-F $_ssh_config"
        fi

        $(scp $_ssh_config $_file_path ${_hostspec}:/tmp/${_component}.sls)
        _file_path="/tmp/${_component}.sls"
    fi

    # TODO is it ok that we stick to python3.6 here ?
    $_cmd python3.6 /opt/seagate/eos-prvsnr/cli/utils/configure-eos.py ${_component} --${_component}-file $_file_path

    local _target_minions='*'
    if [[ -n "$_hostspec" ]]; then
        _target_minions="'*'"
    fi

    # TODO test that
    if [[ $($_cmd rpm -qa salt-master) ]]; then
        $_cmd salt "$_target_minions" saltutil.refresh_pillar
    fi
}


#   eos_pillar_load_default <component> [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Calls `configure-eos.py` util either locally or remotely to reset
#   to a default state the configuration yaml for the specified `component`.
#
#   Prerequisites:
#       - The provisioner repo is installed.
#
#   Args:
#       component: a name of the provisioner repo component.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       timeout: a time to wait until a minion becomes connected to master.
#           Default: `false`.
#
function eos_pillar_load_default {
    set -eu

    local _component="$1"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo")"

    $_cmd python3.6 /opt/seagate/eos-prvsnr/cli/utils/configure-eos.py ${_component} --load-default

    local _target_minions='*'
    if [[ -n "$_hostspec" ]]; then
        _target_minions="'*'"
    fi

    # TODO test that
    if [[ $($_cmd rpm -qa salt-master) ]]; then
        $_cmd salt "$_target_minions" saltutil.refresh_pillar
    fi
}
