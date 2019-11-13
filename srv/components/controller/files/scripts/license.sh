check_license()
{
    tmp_file="/tmp/license"
    # objects name in the xml
    object_basetype="license"
    # list of properties of the object basetype to get their values from the
    # xml e.g. license for virtualization & vds
    property_list=("virtualization" "vds")

    # run command to get the available ports
    cmd_run 'show license'
    # parse xml to get required values of properties
    parse_xml $xml_doc $object_basetype "${property_list[@]}" > $tmp_file

    # Get the status of virtualization license
    virtualization_license=`cat $tmp_file | awk '{ print $1 }'`
    vds_license=`cat $tmp_file | awk '{ print $2 }'`
    [[ $virtualization_license = "Enabled" ]] || {
        echo "Virtualization license is not installed."
        exit 1
    }
    # Get the status of vds license
    [[ $vds_license = "Enabled" ]] || {
        echo "VDS license is not installed."
        exit 1
    }
}