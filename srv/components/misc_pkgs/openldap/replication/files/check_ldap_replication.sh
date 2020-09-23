#!/bin/sh
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


# You should provide Host_list in a file,and give this file as a argument to script.say there are three nodes in cluster with A,B and c.file that contains this hosts should look like below.
# suppose file created is hostlist.txt, cat hostlist.txt should be
# hostname -f  of A
# hostname -f of B
# hostname -f of c

BASEDIR=$(dirname "${BASH_SOURCE}")
cluster_replication=true

function usage { 
  echo "Usage: [-s <provide file containing hostnames of nodes in cluster>],[-p <ldap password>]" 1>&2; exit 1;
}

function trap_handler {
    exit_code=$?

    if [[ 0 != ${exit_code} ]]; then
      echo "***** ERROR! *****"
      if [[ 10 != ${exit_code} ]]; then
        echo Cleaning up temporary account for replication
        ldapdelete -x -w $ldappasswd -r "o=sanity-test-repl-account,ou=accounts,dc=s3,dc=seagate,dc=com" -D "cn=sgiamadmin,dc=seagate,dc=com" -H ldap://$node1 || exit 1
        echo "******************"
      fi
    fi
}
trap trap_handler ERR EXIT

while getopts ":s:p:" o; do
    case "${o}" in
        s)
            host_list=${OPTARG}
            ;;
        p)
            ldappasswd=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ ! -s "$host_list" ]
then
  echo "file $host_list is empty"
  exit 10
fi

echo "Check Ldap replication for below nodes"

while read p; do
  echo "$p"
done <$host_list

#add account

node1=$(head -n 1 $host_list)

ldapadd -w $ldappasswd -x -D "cn=sgiamadmin,dc=seagate,dc=com" -f ${BASEDIR}/create_replication_account.ldif -H ldap://$node1 || exit 0

#adding some delay for successful replication
sleep 5s

# check replication on node 2
while read node; do
  output=$(ldapsearch -b "o=sanity-test-repl-account,ou=accounts,dc=s3,dc=seagate,dc=com" -x -w $ldappasswd -D "cn=sgiamadmin,dc=seagate,dc=com" -H ldap://$node) || echo "failed to search"
  if [[ $output == *"No such object"* ]]
  then
    cluster_replication=false
    echo "Replication is not setup properly on node $node"
    exit 100
  else
    echo "Replication is setup properly on node $node"
  fi
done <$host_list

if [ "$cluster_replication" = true ]
then
  echo "Replication is setup properly on cluster"
else
   echo "Setup replication on nodes,which are not configured correctly for replication"
fi

#delete account created
ldapdelete -x -w $ldappasswd -r "o=sanity-test-repl-account,ou=accounts,dc=s3,dc=seagate,dc=com" -D "cn=sgiamadmin,dc=seagate,dc=com" -H ldap://$node1 || exit 1
