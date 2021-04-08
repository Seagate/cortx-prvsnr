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


set -eu

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
repo_root_dir="$(realpath $script_dir/../../../)"

agent_dir="$script_dir/agent"

IMAGE_VERSION=0.0.1

IMAGE_NAME=seagate/cortx-prvsnr-jenkins-inbound-agent
IMAGE_TAG="$IMAGE_VERSION"
IMAGE_NAME_FULL="$IMAGE_NAME":"$IMAGE_VERSION"

CONTAINER_NAME=cortx-prvsnr-jenkins-agent

DOCKER_SOCKET=/var/run/docker.sock

creds_f="$agent_dir"/credentials
work_dir=
verbosity=0

juser=
japitoken=


function trap_handler_exit {
    ret=$?

    if [[ $ret -ne 0 ]]; then
        echo "***** FAILED!! *****"
        echo "Exiting with return code: $ret"
    else
        echo "Exiting with return code: $ret"
    fi
}
trap trap_handler_exit EXIT


function usage {
  echo "\
Usage: $0 [options] jenkins-url agent-name

Options:
  -h,  --help               print this help and exit
  -c,  --creds-file FILE    path to a file with jenkins credentials
                            at the first line USER:APITOKEN,
                                default: $creds_f
  -w,  --work-dir DIR       path to a directory to use as a jenkins root,
                            will be bind to a container. Should be writeable
                            for the current user.
                                default: (detected automatically)
  -v,  --verbose            be more verbose
"
}


function check_file {
    local _file="$1"
    if [[ ! -f "$_file" ]]; then
        >&2 echo "'$_file' not a file"
        exit 5
    fi
}

function check_file_exists {
    local _file="$1"
    if [[ ! -e "$_file" ]]; then
        >&2 echo "no file '$_file'"
        exit 5
    else
        check_file "$_file"
    fi
}

function parse_args {
    set -eu

    ! getopt --test > /dev/null
    if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
        >&2 echo 'Error: getopt is not functional.'
        exit 1
    fi

    local _opts=hc:w:v
    local _long_opts=help,creds-file:,work-dir:,verbose

    local _getopt_res
    ! _getopt_res=$(getopt --name "$0" --options=$_opts --longoptions=$_long_opts -- "$@")
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        exit 2
    fi

    # TODO why eval here
    eval set -- "$_getopt_res"

    while true; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -c|--creds-file)
                creds_f="$2"
                check_file_exists "$creds_f"
                shift 2
                ;;
            -w|--work-dir)
                work_dir="$(realpath $2)"
                shift 2
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
                >&2 echo "Runtime error"
                exit 3
                ;;
            *)
                >&2 echo "Parser error"
                exit 3
        esac
    done

    if [[ $# -ne 2 ]]; then
        >&2 "$0: wrong number of positional arguments provided: $@"
        usage
        exit 2
    fi

    jenkins_url="$1"
    agent_name="$2"
}

parse_args "$@"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi


if [[ "$verbosity" -ge 1 ]]; then
    parsed_args=""
    parsed_args+="\n\tcreds_f=$creds_f\n\twork-dir=$work_dir"
    parsed_args+="\n\tverbosity=$verbosity"
    parsed_args+="\n\tjenkins_url=$jenkins_url\n\tagent_name=$agent_name"

    echo -e "Parsed arguments:\n$parsed_args"
fi


IFS=':' read -ra creds <<<"$(head -n1 "$creds_f")"
juser="${creds[0]}"
japitoken="${creds[1]}"

uid="$(id -u)"
gid="$(id -g)"

docker build -t "$IMAGE_NAME_FULL" \
    --build-arg "uid=$uid" \
    --build-arg "gid=$gid" \
    -f "$agent_dir"/Dockerfile.inbound-agent "$agent_dir"


IFS=':' read -ra agent_params <<<"$( \
    curl -L -s -u "$juser":"$japitoken" \
    -X GET "${jenkins_url}/computer/agent1/jenkins-agent.jnlp" \
    | sed "s/.*<application-desc main-class=\"hudson.remoting.jnlp.Main\"><argument>\([a-z0-9]*\).*<argument>-workDir<\/argument><argument>\([^<]*\).*/\1:\2/"
)"
agent_secret="${agent_params[0]:-}"
agent_work_dir="${agent_params[1]:-}"

if [[ -z "$agent_secret" || -z "$agent_work_dir" ]]; then
    >&2 "$0: remote agent is not yet configured (no secret and/or working dir is set)"
fi

# TODO API to provide that remote setting to a user
if [[ -n "$work_dir" ]]; then
    if [[ "$agent_work_dir" != "$work_dir" ]]; then
        >&2 "$0: remote agent working dir settings '$agent_work_dir' and the local one "$work_dir" are different"
        exit 1
    fi
else
    work_dir="$agent_work_dir"
fi

docker run --init -d \
    -v "$DOCKER_SOCKET":"$DOCKER_SOCKET" \
    -v "$work_dir":"$work_dir" \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME_FULL" \
    -url "$jenkins_url" \
    -workDir="$work_dir" \
    "$agent_secret" "$agent_name"
