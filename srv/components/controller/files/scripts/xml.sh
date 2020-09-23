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


xml_cmd="/usr/bin/xmllint"
xml_doc="$logdir/tmp.xml"

validate_xml()
{
    echo "validate_xml():$xml_doc " >> $logfile
    [[ `$xml_cmd --noout $xml_doc` ]] && echo "Invalid XML input" && exit 1 
    echo "validate_xml():done - $xml_doc" >> $logfile
}

cli_status_get()
{
    echo "cli_status_get(): $xml_doc" >> $logfile
    node_cnt=`$xml_cmd --xpath 'count(//PROPERTY[@name="response-type"])' $xml_doc`
    status=`$xml_cmd --xpath 'string(//PROPERTY[@name="response-type"]['$node_cnt'])' $xml_doc`
    status_msg=`$xml_cmd --xpath 'string(//PROPERTY[@name="response"]['$node_cnt'])' $xml_doc`
    [[ $status == "Success" ]] || {
        echo "Command failed on the controller with following error:"
        echo "$status_msg"
        exit 1
    }
    echo "cli_status_get(): Command run successfully" >> $logfile
}

parse_xml()
{
    echo "parse_xml(): parsing $xml_doc" >> $logfile
    _bt=$2
    shift 2
    _elements=("$@")
    echo "parse_xml(): basetype=$_bt, _elements=("${_elements[@]}")" >> $logfile
    _cnt=`$xml_cmd --xpath 'count(/RESPONSE/OBJECT[@basetype="'$_bt'"])' $xml_doc`
    for i in $(seq 1 $_cnt)
    do
        echo "parse_xml(): cnt=$_cnt, loop:$i" >> $logfile
        values=()
        for e in "${_elements[@]}"
        do
            av=`$xml_cmd --xpath '/RESPONSE/OBJECT[@basetype="'$_bt'"]['$i']\
               /PROPERTY[@name="'$e'"]/text()' $xml_doc 2>/dev/null`
            echo "parse_xml(): loop:$i, element=$e, av=$av" >> $logfile
            [ "$av" = "" ] && {
               echo "parse_xml(): element=$e has no value" >> $logfile
               av="N/A"
            }
            values+=($av)
        done
        echo "parse_xml(): end of loop for elements, values=("${values[@]}")" >> $logfile
        echo ${values[@]}
    done
    echo "parse_xml(): done" >> $logfile
}