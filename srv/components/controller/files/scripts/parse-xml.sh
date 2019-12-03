#!/bin/bash

validate_xml()
{
    xml_doc=$1
    [[ `$xml_cmd --noout $xml_doc` ]] && echo "Invalid XML input" && exit 1 
}

cli_status_get()
{
    _xml_doc=$1
    node_cnt=`$xml_cmd --xpath 'count(//PROPERTY[@name="response-type"])' $_xml_doc`
    status=`$xml_cmd --xpath 'string(//PROPERTY[@name="response-type"]['$node_cnt'])' $_xml_doc`
    status_msg=`$xml_cmd --xpath 'string(//PROPERTY[@name="response"]['$node_cnt'])' $_xml_doc`
    [[ $status == "Success" ]] || {
        echo "Command failed on the controller with following error:"
        echo "$status_msg"
        exit 1
    }
    echo "Command run successfully"
}

parse_xml()
{
    _xml_doc=$1
    _bt=$2
    shift 2
    _elements=("$@")
    _cnt=`xmllint --xpath 'count(/RESPONSE/OBJECT[@basetype="'$_bt'"])' $_xml_doc`
    for i in $(seq 1 $_cnt)
    do
        values=()
        for e in "${_elements[@]}"
        do
            values+=(`xmllint --xpath '//PROPERTY[@name="'$e'"]['$i']/text()' $_xml_doc`)
        done
        echo ${values[@]}
    done
}