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

IMAGE_VERSION=0.0.1

IMAGE_NAME=seagate/cortx-prvsnr-jenkins
IMAGE_TAG="$IMAGE_VERSION"
IMAGE_NAME_FULL="$IMAGE_NAME":"$IMAGE_VERSION"

CONTAINER_NAME=cortx-prvsnr-jenkins

inputs_f="$script_dir"/jenkins_inputs
jenkins_tmpl_f="$script_dir"/jenkins.yaml.tmpl
jenkins_f="$script_dir"/jenkins.yaml


if [[ ! -f "$inputs_f" ]]; then
    >&2 echo "'$_file' not a file"
    exit 5
fi


function parse_input {
    local _param="$1"
    echo "$(grep "${_param}" "$inputs_f" | head -n1 | sed "s/${_param}=\(.*\)/\1/")"
}

function set_param {
    local _param="$1"
    local _value="${2:-}"
    sed -i "s/{{ ${_param} }}/$_value/g" "$jenkins_f"
}


params=("ADMIN_EMAIL_ADDRESS" "JENKINS_URL" "SMTP_SERVER" "SMTP_USER" "SMTP_PASSWORD")

cp -f "$jenkins_tmpl_f" "$jenkins_f"

for param in "${params[@]}"; do
    set_param "$param" "$(parse_input "$param")"
done

docker build -t "$IMAGE_NAME_FULL" -f "$script_dir"/Dockerfile.jenkins "$script_dir"

docker run --rm -d -p 8080:8080 -p 50000:50000 \
    --name "$CONTAINER_NAME" \
    -v jenkins_home:/var/jenkins_home "$IMAGE_NAME_FULL"