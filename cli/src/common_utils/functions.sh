#!/bin/bash
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#


log_file="${LOG_FILE:-/dev/null}"
if [[ ! -e "$log_file" ]]; then
    mkdir -p $(dirname "${log_file}")
    touch "${log_file}"
fi

# rpm package places scripts in parent folder
cli_scripts_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
pparent_dir=$(cd $cli_scripts_dir/../ && pwd)
if [[ "$(basename ${pparent_dir})" == 'src' ]]; then
    repo_root_dir="$(realpath $cli_scripts_dir/../../../)"
else
    repo_root_dir="$(realpath $cli_scripts_dir/../../)"
fi

cat > /etc/profile.d/set_path_env << EOM
#!/bin/bash
echo $PATH | grep -q "/usr/local/bin" || export PATH=$PATH:/usr/local/bin
EOM
. /etc/profile.d/set_path_env

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
default_ssh_conf="/root/.ssh/config"
default_ssh_disabled="false"
srvnode_1_hostname=
srvnode_2_hostname=

base_options_usage="\
  -h,  --help                     print this help and exit
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
            _level=trace
            ;;
        debug)
            _verbosity=1
            _level=debug
            ;;
        info)
            _verbosity=0
            _level=info
            ;;
        warn)
            _verbosity=0
            _error=true
            _level=warning
            ;;
        error)
            _verbosity=0
            _error=true
            _level=error
            ;;
        *)
            l_error "Unknown log level: $_level"
            exit 5
    esac


    if [[ "$verbosity" -ge "$_verbosity" ]]; then
        _level=$(echo "$_level" | tr '[:lower:]' '[:upper:]')
        _message="[$_level    $(date +'%b %e %H:%M:%S ')]: $_message"

        if [[ "$_error" == true ]]; then
            # Echo message to stderr
            # TODO IMPROVE one-line command
            >&2 echo "$_message"
            logger -t PRVSNR -is "$_message"
            echo "$_message" >> "$log_file"
        else
            echo "$_message" | tee -a "$log_file"
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

    local _opts=nhr:F:sv
    if [[ -n $_add_opts ]]; then
        _opts=$_opts$_add_opts
    fi

    local _long_opts=dry-run,help,remote:,ssh-config:,sudo,verbose
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
            # -S|--singlenode)
            #     singlenode=true
            #     shift
            #     ;;
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


#   user_from_spec <hostspec>
#
#   Extracts and echoes user of the hostspec into stdout.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#
#   Outputs:
#       An extracted user value from hostpec.
#
function user_from_spec {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _hostspec="$1"
    if [[ $_hostspec == *"@"* ]]; then
        IFS='@' read -a _arr <<< $_hostspec
        if [[ "${#_arr[@]}" -eq 2 ]]; then
            _user="${_arr[0]}"
        else
            _user=
        fi
    fi
    echo "$_user"
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

function check_hostname_in_ssh_config {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _hostspec=$1
    local _ssh_config=$1

    if [[ -f "$_ssh_config" ]]; then
        echo "$(grep -A1 -n "Host $_hostspec" $default_ssh_conf | tail -1 | cut -f1 -d-)"
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
    local _hostname_only="${3:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" 2>/dev/null)"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    if [[ "$_hostname_only" == true ]]; then
        hostname --fqdn
    else
        yum -y install iproute >&2

        ip_list="\$(ip addr show scope global up | sed -n "s/.*inet \([^/]\+\).*/\1/p" || true)"
        ifconfig_list="\$(ifconfig 2>/dev/null | sed -n "s/.*inet \([^ ]\+\).*/\1/p" | grep -v 127.0.0.1 || true)"
        hostname="\$(hostname | grep -v 127.0.0.1 || true)"
        echo \$ip_list \$ifconfig_list \$hostname | awk "{for(i = 1; i<=NF; i++) {print \\\$i}}" | sort -u | paste -sd " " -
    fi
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



#   get_reachable_names <hostspec1> <ssh-config> [<hostspec2>]
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
function get_reachable_names {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _hostspec1="${1:-}"
    local _hostspec2="${2:-}"
    local _ssh_config="${3:-}"
    local _hostname_only="${4:-false}"

    local _res=()

    if [[ "$_hostspec1" == "$_hostspec2" ]]; then
        l_error "host1 and host2 can't be the same, provided: $_hostspec1"
        exit 1
    fi

    _host1_addrs="$(collect_addrs "$_hostspec1" "$_ssh_config" $_hostname_only)"
    _host2_addrs="$(collect_addrs "$_hostspec2" "$_ssh_config" $_hostname_only)"

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

    echo "${_res[*]+"${_res[*]}"}"
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
#       bundle_base_url: mark the release as bundle
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
    local _bundle_base_url="${4:-}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    local _repo_base_dir="/etc/yum.repos.d"
    local _repo_base_dir_backup="/etc/yum.repos.d.bak"
    local _project_repos="$repo_root_dir/files/etc/yum.repos.d"

    local _cortx_deps_repo
    local _system_repo
    local _saltstack_repo
    local _epel_repo

    l_info "Installing replacing package repositories '$_hostspec'"


! read -r -d '' _script << EOF
    set -eu
    mkdir -p $(dirname "${log_file}")
    /usr/bin/true > "${log_file}"

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # config custom repos
    yum clean expire-cache
    rm -rf /var/cache/yum

    if [[ -d "$_repo_base_dir" && ! -d "$_repo_base_dir_backup" ]]; then
        cp -R "$_repo_base_dir" "$_repo_base_dir_backup"
    else
        echo -e "\\nWARNING: skip backup creation since backup already exists" | tee -a "$log_file" >&2
    fi

    rm -rf "$_repo_base_dir"

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

    if [[ -n "$_bundle_base_url" ]]; then
        _cortx_deps_repo="${bundle_base_url}/3rd_party"
        _saltstack_repo="${_cortx_deps_repo}/commons/saltstack"
        _epel_repo="${_cortx_deps_repo}/EPEL-7"

! read -r -d '' _script << EOF
    set -eu
    mkdir -p $(dirname "${log_file}")
    /usr/bin/true > "${log_file}"

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    grep -q "Red Hat" /etc/*-release && {
        _system_repo="${bundle_base_url}/rhel7.7"
        # l_info "OS RHEL: Use subscription manager with appropriate subscriptions mentioned in Seagate setup docs to enable required package repositories."
    } || {
        _system_repo="${bundle_base_url}/centos7.7"
    }

    # TODO FIXME EOS-12508 base, extras, updates
    sed "s/baseurl=.*/baseurl=\$_system_repo/g" /etc/yum.repos.d/base.repo
    sed "s/baseurl=.*/baseurl=$_cortx_deps_repo/g" /etc/yum.repos.d/cortx_commons.repo
    sed "s/baseurl=.*/baseurl=$_epel_repo/g" /etc/yum.repos.d/epel.repo
    sed "s/baseurl=.*/baseurl=$_saltstack_repo/g" /etc/yum.repos.d/saltstack.repo
    # # FIXME EOS-12508
    rm -f /etc/yum.repos.d/extras.repo
    rm -f /etc/yum.repos.d/updates.repo
EOF
    fi
}

#   install_salt_repo [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Install salt repository either on the remote host or locally.
#   The function assumes that '../../files/etc/yum.repos.d/saltstack.repo' exists.
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       bundle_base_url: mark the release as bundle
#           Default: `false`.
#
function install_salt_repo {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"
    local _bundle_base_url="${4:-}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    local _repo_base_dir="/etc/yum.repos.d"
    local _repo_base_dir_backup="/etc/yum.repos.d.bak"
    local _salt_repo_file="${_repo_base_dir}/saltstack.repo"
    local _salt_repo_bak_file="${_repo_base_dir_backup}/saltstack.repo.bak"
    # local _salt_repo_url="${SALT_REPO_URL:-https://archive.repo.saltstack.com/py3/redhat/\$releasever/\$basearch/archive/2019.2.0}"
    local _salt_repo_url="${SALT_REPO_URL:-https://repo.saltstack.com/py3/redhat/\$releasever/\$basearch/3002}"
    local _project_repos="$repo_root_dir/files/etc/yum.repos.d"

    if [[ -n "$_bundle_base_url" ]]; then
        _salt_repo_url="${bundle_base_url}/3rd_party/commons/saltstack-3002"
    fi

    l_info "Installing Salt repository '$_hostspec'"
    local _saltstack_repo="/tmp/saltstack.repo"

#name=SaltStack repo for RHEL/CentOS \$releasever
    cat <<EOL > ${_saltstack_repo}
[saltstack]
name=SaltStack repo for RHEL/CentOS
baseurl=${_salt_repo_url}
enabled=1
gpgcheck=1
gpgkey=${_salt_repo_url}/SALTSTACK-GPG-KEY.pub
priority=1
EOL

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # config custom repos
    yum clean expire-cache
    rm -rf /var/cache/yum

    # if [[ -f "$_salt_repo_file" && ! -f "$_salt_repo_bak_file" ]]; then
    #     cp "$_salt_repo_file" "$_salt_repo_bak_file"
    # else
    #     echo -e "\\nWARNING: skip backup creation since backup already exists"
    # fi

    # TODO a temporary fix since later version (2019.2.1) is buggy
    # (https://repo.saltstack.com/#rhel, instructions for minor releases centos7 py3)
    #rpm --import ${_salt_repo_url}/SALTSTACK-GPG-KEY.pub

    echo "_hostspec=$_hostspec"
    if [[ -z "$_hostspec" ]]; then
        #cp -R "$_project_repos/saltstack.repo" "$_repo_base_dir/"
        #echo \${saltstack_repo} > $_repo_base_dir/saltstack.repo
        echo "Creating saltstack repo"
        cp "$_saltstack_repo" "$_repo_base_dir/"
    fi
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script" 2>&1 | tee -a ${LOG_FILE}

    if [[ -n "$_hostspec" ]]; then
        # scp -r -F "$_ssh_config" "$_project_repos/saltstack.repo" "${_hostspec}":"$_repo_base_dir"
        scp -r -F "$_ssh_config" "$_repo_base_dir/saltstack.repo" "${_hostspec}":"$_repo_base_dir"
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
    #systemctl stop iptables6 && systemctl disable iptables6 && systemctl mask iptables6
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
    # TODO install salt-ssh salt-syndic as well as cortx-prvsnr rpm supposes

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
#           Default: `srvnode-1`.
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

    local _multipath_config_file="/etc/multipath.conf"
    local _multipath_config_repo_file="$repo_root_dir/files/etc/multipath.conf"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Installing and Configuring multipath '$_minion_id'"

    if [[ $($_cmd rpm -qa salt-master) ]]; then
        $_cmd salt -t $_timeout "$_minion_id" state.apply system.storage.multipath
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

    # install salt-master/salt-minion
    yum install -y salt-minion salt-master
EOF
    # TODO install salt-ssh salt-syndic as well as cortx-prvsnr rpm supposes

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
#           `github` - installs from Github using the specified
#               version `prvsnr-version`. If the version is not set
#               uses the latest tagged one.                         # FIXME EOS-13293
#           `gitrepo` - establishes local git repo at `/opt/seagate/cortx-prvsnr`
#               pointing to remote repo on Github. This should help use switch between
#               branches for validation of branched changes.
#           `local` - copies local working copy of the repository, assumes
#               that script is a part of it.
#       prvsnr-version: The version of the CORTX provisioner to install. Makes sense only
#           for `github` source for now. Default: not set.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       singlenode: a flag for a singlenode setup mode. Expected values: `true` or `false`.
#           Default: `false`
#       installation-dir: destination installation directory.
#           Default: /opt/seagate/cortx/provisioner
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
    local _installdir="${7:-/opt/seagate/cortx/provisioner}"
    local _dev_repo="${8:-false}"
    local _os_release="rhel-7.7.1908"
    #local _os_release="centos-7.7.1908"
    
    local _prvsnr_repo=
    local _repo_archive_path=
    local _tmp_dir=$(mktemp -d)

    local _cluster_sls_src
    if [[ "$_singlenode" == true ]]; then
        _cluster_sls_src="$_installdir/pillar/samples/singlenode.cluster.sls"
    else
        _cluster_sls_src="$_installdir/pillar/samples/dualnode.cluster.sls"
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
            _prvsnr_version="http://cortx-storage.colo.seagate.com/releases/cortx/github/release/${_os_release}/last_successful/"
        fi
    fi

! read -r -d '' _prvsnr_repo << EOF
[provisioner]
gpgcheck=0
enabled=1
baseurl="$_prvsnr_version"
name=provisioner
EOF

    if [[ "$_repo_src" != "github" && "$_repo_src" != "rpm" && "$_repo_src" != "local" && "$_repo_src" != "gitrepo" ]]; then
        l_error "unsupported repo src: $_repo_src"
        exit 1
    fi

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    local _api_dir="${_installdir}/api/python"
    local _prvsnr_group=prvsnrusers

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # TODO test cases when installation dir is presented and not empty
    # issue #23
    #rm -rvf "$_installdir"
    mkdir -p "$_installdir"
    if [[ "$_repo_src" == "github" ]]; then
        pushd "$_installdir"
            curl "https://github.com/Seagate/cortx-prvsnr/-/archive/${_prvsnr_version}/${_prvsnr_version}.tar.gz" | tar xzf - --strip-components=1
        popd
    elif [[ "$_repo_src" == "gitrepo" ]]; then
        pushd "$_installdir"
            yum install -y git
            git init
            if git remote show origin ; then
                git remote remove origin
            fi

            git remote add origin https://github.com/Seagate/cortx-prvsnr.git
            git fetch origin
            git checkout -B ${_prvsnr_version} origin/${_prvsnr_version} -f
            # git clean -fdx        # Commented because there could be intentional changes in workspace.
            
            # set api
            #   adding provisioner group
            echo "Creating group '$_prvsnr_group'..."
            groupadd -f "$_prvsnr_group"

            echo "Configuring access for provisioner data ..."
            bash "${_api_dir}/provisioner/srv/salt/provisioner/files/post_setup.sh"

            #   install api globally using pip
            pip3 install -U "${_api_dir}"
        popd
    elif [[ "$_repo_src" == "rpm" ]]; then
        echo "$_prvsnr_repo" >/etc/yum.repos.d/prvsnr.repo
        yum install -y cortx-prvsnr
        if curl --output /dev/null --silent --head --fail "$_prvsnr_version/RELEASE.INFO"; then
            wget $_prvsnr_version/RELEASE.INFO -O /etc/yum.repos.d/RELEASE_FACTORY.INFO
        fi
         yum install -y python36-cortx-prvsnr
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
#   Configures network on the CORTX stack node either on local or remote host.
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
#           Default: /opt/seagate/cortx/provisioner
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
    local _installdir="${5:-/opt/seagate/cortx/provisioner}"

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


#   configure_salt <minion-id> [<hostspec> [<ssh-config> [<sudo> [<is-primary> [<master-host> [<installation-dir>]]]]]]
#
#   Configures salt-minion (ans salt-master if `is-primary` set to `true`) either on the local or remote host.
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
#       is-primary: A flag to switch between primary / secondary CORTX stack nodes.
#           Default: `true`.
#       master-host: A resolvable (from within the minion's host) domain name or IP of the salt master.
#           Default: not set.
#       installation-dir: destination installation directory.
#           Default: /opt/seagate/cortx/provisioner
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
    local _primary="${5:-true}"
    local _primary_host="${6:-srvnode-1}"
    local _installdir="${7:-/opt/seagate/cortx/provisioner}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Configuring salt on '$_hostspec': minion-id $_minion_id, is-primary $_primary, master host $_primary_host"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    pushd "$_installdir"
        # re-config salt-master
        if [[ ! -f /etc/salt/master.org ]]; then
            mv -f /etc/salt/master /etc/salt/master.org
            cp srv/provisioner/salt_master/files/master /etc/salt/master
        fi

        if [[ "$_primary" == true ]]; then
            systemctl enable salt-master
            systemctl restart salt-master
        fi

        # re-config salt minion
        if [[ ! -f /etc/salt/minion.org ]]; then
            mv -f /etc/salt/minion /etc/salt/minion.org
            cp srv/provisioner/salt_minion/files/minion /etc/salt/minion
        fi

        if [[ -n "$_primary_host" ]]; then
            sed -i "s/^master: .*/master: $_primary_host/g" /etc/salt/minion
        fi

        if [[ "$_primary" == true ]]; then
            cp -f srv/provisioner/salt_minion/files/grains.primary /etc/salt/grains
        else
            cp -f srv/provisioner/salt_minion/files/grains.secondary /etc/salt/grains
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


#   accept_salt_key [<minion-ids> [<hostspec> [<ssh-config> [<sudo> [<timeout>]]]]]
#
#   Makes keys for the specified list of minions accepted by the salt-master.
#
#   Salt-master might be either local or remote host.
#
#   Prerequisites:
#       - SaltStack is installed.
#       - The provisioner repo is installed.
#       - CORTX stack salt-master/salt-minions are configured.
#
#   Args:
#       minion-ids: a space separated list minion ids which keys should be accepted.
#           Default: `srvnode-1`.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       timeout: a time to wait until a salt-minion becomes connected to salt-master.
#           Default: `false`.
#
function accept_salt_key {
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    local _script

    local _id="${1:-srvnode-1}"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"
    local _timeout="${5:-30}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Accepting minion id $_id on salt-master '$_hostspec', timeout $_timeout"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    try=1
    echo -e "\\nINFO: waiting for salt-minion $_id to become connected to salt-master"
    until salt-key --list-all | grep $_id >/dev/null 2>&1
    do
        if [[ "\$try" -gt "$_timeout" ]]; then
            echo -e "\\nERROR: salt-minion $_id seems not connected after $_timeout seconds."
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
        echo -e "\\nINFO: no key acceptance is needed for minion $_id."
        salt-key --list-all >&2
        exit 0
    fi

    salt-key -y -a $_id
    echo -e "\\nINFO: Key $_id is accepted."

    # TODO move that to a separate API
    echo -e "\\nINFO: waiting for minion $_id to become ready"
    try=1; tries=10
    until salt -t 1 $_id test.ping >/dev/null 2>&1
    do
        if [[ "\$try" -gt "\$tries" ]]; then
            echo -e "\\nERROR: minion $_id seems still not ready after \$tries checks."
            exit 1
        fi
        echo -n "."
        try=\$(( \$try + 1 ))
    done
    echo -e "\\nINFO: Minion $_id started." 
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script" 2>&1| tee -a "$log_file"
}


#   cortx_pillar_show_skeleton <component> [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Calls provisioner api cli either locally or remotely to dump a skeleton
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
#       timeout: a time to wait until a salt-minion becomes connected to salt-master.
#           Default: `false`.
#
function cortx_pillar_show_skeleton {
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
    $_cmd provisioner configure_cortx ${_component} --show
}


#   cortx_pillar_update <component> <file-path> [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Calls provisioner api cli either locally or remotely to update
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
function cortx_pillar_update {
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
    $_cmd provisioner configure_cortx ${_component} --source $_file_path

    local _target_minions='*'
    if [[ -n "$_hostspec" ]]; then
        _target_minions="'*'"
    fi

    # TODO test that
    if [[ $($_cmd rpm -qa salt-master) ]]; then
        $_cmd salt "$_target_minions" saltutil.refresh_pillar
    fi
}


#   cortx_pillar_load_default <component> [<hostspec> [<ssh-config> [<sudo>]]]
#
#   Calls provisioner api cli either locally or remotely to reset
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
#       timeout: a time to wait until a salt-minion becomes connected to salt-master.
#           Default: `false`.
#
function cortx_pillar_load_default {
    set -eu

    local _component="$1"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo")"

    $_cmd provisioner configure_cortx ${_component} --reset

    local _target_minions='*'
    if [[ -n "$_hostspec" ]]; then
        _target_minions="'*'"
    fi

    # TODO test that
    if [[ $($_cmd rpm -qa salt-master) ]]; then
        $_cmd salt "$_target_minions" saltutil.refresh_pillar
    fi
}

# TODO TEST EOS-12508
#   update_release_pillar <target_release>
#   e.g. update_release_pillar integration/centos-7.7.1908/859
#
#   Updates release pillar with provided target release
#
#   Prerequisites:
#       - The provisioner repo is installed.
#
#   Args:
#       target_release: target release version for all the CORTX components
#       bundled_release: mark the release as bundle
function update_release_pillar {
    set -eu

    local _release_ver="$1"
    local _bundled_release="${2:-false}"

    #local _release_sls="${repo_root_dir}/pillar/components/release.sls"

    #_line="$(grep -n target_build $_release_sls | awk '{ print $1 }' | cut -d: -f1)"
    #sed -ie "${_line}s/.*/    target_build: $(echo ${_release_ver} | sed 's_/_\\/_g')/" $_release_sls
    provisioner pillar_set release/target_build \"${_release_ver}\"

    if [[ "$_bundled_release" == true ]]; then
        provisioner pillar_set release/type \"bundle\"
    fi
}

#   update_cluster_pillar_hostname <srvnode-#> <srvnode-# hostname>
#   e.g. update_cluster_pillar_hostname srvnode-1  smc-vm1.colo.seagate.com
#
#   Updates cluster pillar with provided hostname for the provided srvnode
#
#   Prerequisites:
#       - The provisioner repo is installed.
#
#   Args:
#       srvnode-#: srvnode-1 or srvnode-2
#       srvnode-# hostname: hostname to be updated for srvnode-# in cluster.sls
function update_cluster_pillar_hostname {
    set -eu

    local _node="$1"
    local _host="$2"
    local _cluster_sls="${repo_root_dir}/pillar/components/cluster.sls"

    #_line=`grep -A1 -n "${_node}:" $_cluster_sls | tail -1 | cut -f1 -d-`
    #sed -ie "${_line}s/.*/    hostname: ${_host}/" $_cluster_sls
    provisioner pillar_set cluster/${_node}/hostname \"${_host}\"
}

#  disable_default_sshconfig
#
#  Take backup of default ssh config file shipped with cortx-prvsnr-cli rpm
function disable_default_sshconfig {

    if [[ -f "$default_ssh_conf" ]]; then
        mv $default_ssh_conf ${default_ssh_conf}.bak
    fi
}

#  enable_default_sshconfig
#
#  Restor the default ssh config file shipped with cortx-prvsnr-cli rpm
function enable_default_sshconfig {

    if [[ -f "${default_ssh_conf}.bak" ]]; then
        mv "${default_ssh_conf}.bak" $default_ssh_conf
    fi
}

#  setup_ssh
#
#  Sets up passwordless ssh between the nodes provided in ssh config file.
#
#  Prerequisites:
#     default ssh config file present at /root/.ssh/config
function setup_ssh {
    set -eu

    l_info "Setting up passwordless ssh configuration"
    srvnode_1_hostname=`hostname -f`
    local _srvnode_1_user=`who | awk '{ print $1 }'`
    srvnode_2_hostname=`hostname_from_spec $srvnode_2_hostspec`

    if [[ $srvnode_1_hostname != *"."* ]]; then
        l_error "Short hostnames are not supported, please provide FQDN for srvnode-1"
    fi

    if [[ $srvnode_2_hostname != *"."* ]]; then
        l_error "Short hostnames are not supported, please provide FQDN for srvnode-2"
    fi

    #local _srvnode_2_user=`user_from_spec $srvnode_2_hostspec`
    # Ensure user name is root on both the hosts.
    #if [[ "$_srvnode_1_user" != "root" || "$_srvnode_2_user" != "root" ]]; then
    #    l_error "This command requires user to be root"
    #    l_error "Please rerun the command with root user"
    #    exit 1
    #fi
    

    if [[ ! -f "$default_ssh_conf" ]]; then
        l_error "ssh config file not found: $default_ssh_conf"
        exit 1
    fi
    
    #Backup original ssh config file
    cp "$default_ssh_conf" "${default_ssh_conf}.bak"

    # update ssh_config file with srvnode-1 details
    sed -i "s/Host srvnode-1 .*/Host srvnode-1 ${srvnode_1_hostname}/" $default_ssh_conf
    line=`grep -A1 -n "Host srvnode-1" $default_ssh_conf | tail -1 | cut -f1 -d-`
    sed -ie "${line}s/.*/    HostName ${srvnode_1_hostname}/" $default_ssh_conf

    # update ssh_config file with srvnode-2 details
    sed -i "s/Host srvnode-2 .*/Host srvnode-2 ${srvnode_2_hostname}/" $default_ssh_conf
    line=`grep -A1 -n "Host srvnode-2" $default_ssh_conf | tail -1 | cut -f1 -d-`
    sed -ie "${line}s/.*/    HostName ${srvnode_2_hostname}/" $default_ssh_conf

    # Check if the ssh works without password from node-1 to node-2
    ssh -q -o "ConnectTimeout=5" $srvnode_2_hostspec exit || {
        l_error "$srvnode_2_hostspec not reachable"
        l_error "Couldn't do the ssh passwordless setup from $srvnode_1_hostname to $srvnode_2_hostspec"
        l_error "please provide correct hostname using --srvnode-2 option"
        l_error " OR use -F option to provide the correct ssh config file"
        #Backup original ssh config file
        cp "${default_ssh_conf}.bak" "$default_ssh_conf"
        exit 1
    }

    # Copy the updated ssh config file to second node
    scp $default_ssh_conf $srvnode_2_hostspec:$default_ssh_conf

    # Check if the ssh works without password from node-2 to node-1
    ssh -q -o "ConnectTimeout=5" $srvnode_2_hostspec \
        "ssh -q -o ConnectTimeout=5 srvnode-1 exit; exit" || {
        l_error "$srvnode_1_hostname is not reachable from $srvnode_2_hostspec"
        l_error "Couldn't do the ssh passwordless setup"
        l_error "Ensure the hosts are able to communicate with each other"
        #Backup original ssh config file
        cp "${default_ssh_conf}.bak" "$default_ssh_conf"
        exit 1
    }
    
    echo "ssh passwordless setup done successfully" | tee -a "$log_file"
}
#   set_node_id <hostspec> [<ssh-config> [<sudo> ]]
#
#   Generates and assigns a node_id in salt grains.
#
#   Prerequisites:
#       - SaltStack is installed.
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
#           Default: /opt/seagate/cortx/provisioner
#
function set_node_id {
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"
    local _installdir="${4:-/opt/seagate/cortx/provisioner}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "NodeID on $_hostspec"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    pushd "$_installdir"
        if [[ ! -e "/opt/seagate/cortx_configs/provisioner_generated/node_id" ]]; then
            mkdir -p /opt/seagate/cortx_configs/provisioner_generated/
            echo "node_id: \$(uuidgen)" > /opt/seagate/cortx_configs/provisioner_generated/node_id
        fi

        if [[ -z "\$(grep "node_id" /etc/salt/grains 2>/dev/null)" ]]; then
            cat /opt/seagate/cortx_configs/provisioner_generated/node_id >> /etc/salt/grains
        fi

        systemctl enable salt-minion
        systemctl restart salt-minion
    popd
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script" 2>&1| tee -a "$log_file"
}

#   set_cluster_id <cluster_id> <hostspec> [<ssh-config> [<sudo> ]]
#
#   Generates and assigns cluster id in salt grains.
#
#   Prerequisites:
#       - SaltStack is installed.
#       - The provisioner repo is installed.
#
#   Args:
#       cluster_id: ID of cluster to be set.
#           Default: not set.
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#       installation-dir: destination installation directory.
#           Default: /opt/seagate/cortx/provisioner
#
function set_cluster_id {
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    local _script

    local _cluster_uuid="${1:-}"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"
    local _installdir="${5:-/opt/seagate/cortx/provisioner}"

    if [[ -z "$_cluster_uuid" ]]; then
        l_error "Set cluster ID cannot be set as blank on $_hostspec"
        exit 1
    fi

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Set cluster ID (${_cluster_uuid}) on $_hostspec"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    pushd "$_installdir"
        if [[ ! -e "/opt/seagate/cortx_configs/provisioner_generated/cluster_id" ]]; then
            mkdir -p /opt/seagate/cortx_configs/provisioner_generated/
        fi
        echo "cluster_id: ${_cluster_uuid}" > /opt/seagate/cortx_configs/provisioner_generated/cluster_id

        if [[ -z "\$(grep "cluster_id" /etc/salt/grains 2>/dev/null)" ]]; then
            cat /opt/seagate/cortx_configs/provisioner_generated/cluster_id >> /etc/salt/grains
        else
            sed -i "s/cluster_id:.*/cluster_id: ${_cluster_uuid}/g" /etc/salt/grains
        fi

        systemctl enable salt-minion
        systemctl restart salt-minion
    popd
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}


#   configure_provisioner_api_logs [<hostspec> [<ssh-config> [<sudo> [<insrallation-dir>]]]]
#
#   Configures rsyslog to capture provisioner logs in custom log file
#
#   TODO IMPROVE this function is not necessary since we have
#        provisioner.config for the same logic,
#        should be a part of salt based provisioner configuration
#
#   Args:
#       hostspec: remote host specification in the format [user@]hostname.
#           Default: not set.
#       ssh-config: path to an alternative ssh-config file.
#           Default: not set.
#       sudo: a flag to use sudo. Expected values: `true` or `false`.
#           Default: `false`.
#
function configure_provisioner_api_logs {
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    local _script

    local _hostspec="${1:-}"
    local _ssh_config="${2:-}"
    local _sudo="${3:-false}"
    local _installdir="${4:-/opt/seagate/cortx/provisioner}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    l_info "Configuring rsyslog to capture provsioner api logs '$_hostspec'"

! read -r -d '' _script << EOF
    set -eu

    if [[ "$verbosity" -ge 2 ]]; then
        set -x
    fi

    # TODO IMPROVE seems not necessary here
    # Install rsyslog
    #yum -y install rsyslog         # Installs rsyslog 8.24 from base

    # Preapare to install rsyslog 8.40 from common_uploads repo
    salt-call state.apply system.prepare
    salt-call state.apply provisioner.config
EOF

    if [[ -n "$_hostspec" ]]; then
        _script="'$_script'"
    fi

    $_cmd bash -c "$_script"
}

#   update_bmc_ip <srvnode-#>
#   e.g. update_bmc_ip srvnode-1
#
#   Updates cluster pillar with provided hostname for the provided srvnode
#
#   Prerequisites:
#       - The provisioner repo is installed.
#
#   Args:
#       srvnode-#: srvnode-1 or srvnode-2
#       srvnode-# hostname: hostname to be updated for srvnode-# in cluster.sls
function update_bmc_ip {
    set -eu

    if [[ "$verbosity" -ge "2" ]]; then
        set -x
    fi

    local _node="${1:-srvnode-1}"
    local _hostspec="${2:-}"
    local _ssh_config="${3:-}"
    local _sudo="${4:-false}"
    local _installdir="${5:-/opt/seagate/cortx/provisioner}"

    local _cmd="$(build_command "$_hostspec" "$_ssh_config" "$_sudo" 2>/dev/null)"

    local _cluster_sls_path=${_installdir}/pillar/components/cluster.sls
    if [[ -f "${_installdir}/pillar/user/groups/all/cluster.sls" ]]; then
        _cluster_sls_path=${_installdir}/pillar/user/groups/all/cluster.sls
    fi

    # Install ipmitool package
    if [[ -n "$_hostspec" ]]; then
        ${_cmd} "rpm -qi ipmitool > /dev/null || yum install -y ipmitool"
    else
        rpm -qi ipmitool > /dev/null || yum install -y ipmitool
    fi

    l_info "Acquire BMC IP on NodeID: ${_hostspec}"

    local _ip_line=""
    if [[ -n "$_hostspec" ]]; then
        _ip_line=$($_cmd "ipmitool lan print 1|grep -oP 'IP Address.+:.*\d+'")
    else
        _ip_line=$(ipmitool lan print 1|grep -oP 'IP Address.+:.*\d+')
    fi

    local _ip=$(echo ${_ip_line}|cut -f2 -d':'|tr -d ' ')

    if [[ -n "$_ip" && "$_ip" != "0.0.0.0" ]]; then
        l_info "BMC_IP: ${_ip}"
        provisioner pillar_set cluster/${_node}/bmc/ip \"${_ip}\"
    else
        l_info "BMC_IP is not configured"
    fi
}
