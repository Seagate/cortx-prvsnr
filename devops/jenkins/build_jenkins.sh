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

docker build -t "$IMAGE_NAME_FULL" -f "$script_dir"/Dockerfile.jenkins "$script_dir"


docker run -d -p 8080:8080 -p 50000:50000 \
    --name "$CONTAINER_NAME" \
    -v jenkins_home:/var/jenkins_home "$IMAGE_NAME_FULL"
