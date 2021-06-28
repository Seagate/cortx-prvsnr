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


set -eux

echo 'http://12345' | sed 's~https://~~'


JENKINS_URL="${JENKINS_URL:-}"
JENKINS_URL_TRUSTED="${JENKINS_URL_TRUSTED:-}"
JENKINS_CERT='jenkins.cert'


if [[ -z "$JENKINS_URL_TRUSTED" ]]; then
    echo "$0: not trusted url, exiting"
    exit 0
fi

if [[ -z "$JENKINS_URL" ]]; then
    echo "$0: No url, exiting"
    exit 0
fi

j_url=$(echo "$JENKINS_URL" | sed 's~https://~~; s~/\+$~~g')

echo -n | openssl s_client -connect "$j_url" | \
    sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > "$JENKINS_CERT"


keytool -import -trustcacerts -keystore "${JAVA_HOME}/jre/lib/security/cacerts" \
    -storepass changeit -noprompt -alias jenkinscert -file "$JENKINS_CERT"

rm -f "$JENKINS_CERT"
