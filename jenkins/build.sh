#!/bin/bash
#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

set -e

PROG=$(basename "$0")
SCRIPT_DIR=$(realpath $(dirname "$0"))
BASE_DIR=$SCRIPT_DIR/..
BUILD_NUMBER=
GIT_VER=

usage() {
    echo """usage: $PROG[-v version] [-g git_version] [-b build_number]""" 1>&2;
    exit 1;
}

# Check for passed in arguments
while getopts ":g:v:b:" o; do
    case "${o}" in
        v)
            VER=${OPTARG}
            ;;
        g)
            GIT_VER=${OPTARG}
            ;;
        b)
            BUILD_NUMBER=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

[ -z $"$GIT_VER" ] && GIT_VER="$(git rev-parse --short HEAD)" \
        || GIT_VER="${GIT_VER}_$(git rev-parse --short HEAD)"
[ -z "$VER" ] && VER="2.0.0"
[ -z "$BUILD_NUMBER" ] && BUILD_NUMBER=1
REL="${BUILD_NUMBER}_${GIT_VER}"

rpm -q rpm-build > /dev/null || {
    echo "error: rpm-build is not installed. Install rpm-build and run $PROG"
    exit 1;
}

# Create version file
echo $VER > "$BASE_DIR"/VERSION
/bin/chmod +rx "$BASE_DIR"/VERSION
/bin/chmod +x "$BASE_DIR"/src/setup/cortx_deploy

cd $BASE_DIR

./setup.py bdist_rpm --release="$REL"
