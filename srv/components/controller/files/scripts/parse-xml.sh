cli_status_get()
{
    _xml_doc=$1
    status=`$xml_cmd -xpath '/RESPONSE/OBJECT/PROPERTY[@name="response-type"]/text()' $_xml_doc`
    [[ $status != "Success" ]] && echo "Command failed on the controller" && exit 1
    echo "Command run successfully"
}

parse_version()
{
    _xml_doc=$1
    _elements=$2
    _xpath_exp="'/RESPONSE/OBJECT[@basetype=\"$_basetype\"]/PROPERTY[@name=\"$_element\"]/text()'"
    # Parse command output
    ret_txt=`$xml_cmd -xpath $_xpath_exp $_xml_doc`

}

parse_xml()
{
    #TODO: accept object attribut and property attribute at cmd line
    _xml_doc=$1
    _element=$2
    _xpath_exp="'/RESPONSE/OBJECT/PROPERTY[@name=\"$_element\"]/text()'"
    # Parse command output
    ret_txt=`$xml_cmd -xpath $_xpath_exp $_xml_doc`
}

validate_xml()
{
    xml_doc=$1
    [[ `$xml_cmd $xml_doc` ]] && echo "Invalid XML input" && exit 1 
}