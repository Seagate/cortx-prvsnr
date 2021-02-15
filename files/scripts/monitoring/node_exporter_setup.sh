#!/bin/bash

usage()
{
	echo "\
Usage:
Required Arguments:
	-pi|--pub_ip    IP address of the public data network.
	-vi|--pvt_ip    IP address of the private data network.
Optional Arguments:
	-h|--help   	brief info about script
"
}

help()
{
	echo "\
---------------------------------------------------------------------------------
1. The command must be run on the linux system to be monitored / target nodes.
2. The system must have 3 network interfaces.
-------------------- Sample command ---------------------------------------------
$ sh node_exporter_setup.sh -pi 192.168.14.157 -vi 192.168.31.255

"
}


pub_ip_addr=
pvt_ip_addr=

while [[ $# -gt 0 ]]; 
do
	case $1 in 
		-h|--help) usage; help; exit 0
		;;
		-pi|--pub_ip)
			[ -z "$2" ] && echo "Error: IP address of private data network not provided" && exit 1;
			pub_ip_addr="$2"
			shift 2
		;;
		-vi|--pvt_ip)
			[ -z "$2" ] && echo "Error: IP address of private data network not provided" && exit 1;
			pvt_ip_addr="$2"
			shift 2
		;;
		*) 
			echo "Invalid option $1"; usage; exit 1;
		;;
	esac
done

echo -e "\n\t***** INFO: Installing Node Exporter *****"

useradd --no-create-home --shell /bin/false node_exporter
mkdir /etc/node_exporter
mkdir /etc/node_exporter/textfile_collector
mkdir /var/lib/node_exporter
chown node_exporter:node_exporter /etc/node_exporter
chown node_exporter:node_exporter /var/lib/node_exporter

curl -LO https://github.com/prometheus/node_exporter/releases/download/v1.0.1/node_exporter-1.0.1.linux-amd64.tar.gz
tar -xvf node_exporter-1.0.1.linux-amd64.tar.gz
mv node_exporter-1.0.1.linux-amd64 node_exporter_files
rm -rf node_exporter-1.0.1.linux-amd64.tar.gz
cp node_exporter_files/node_exporter /usr/local/bin
chown node_exporter:node_exporter /usr/local/bin/node_exporter

dir_size_script_path='/etc/node_exporter/dir_size.sh'
cat << EOL > ${dir_size_script_path}
du -sb /var/log /var /tmp | sed -ne 's/^\([0-9]\+\)\t\(.*\)$/node_directory_size_bytes{directory="\2"} \1/p'
EOL


ping_test_script_path='/etc/node_exporter/ping_test.sh'
cat << EOL > ${ping_test_script_path}
#!/bin/bash
pub_ip=$pub_ip_addr
pvt_ip=$pvt_ip_addr
ip_list=(\$pub_ip \$pvt_ip)
int_name=("public_data_ip" "private_data_ip")
count=0
while [ \$count -le 1 ]
do
    ping_status=\`ping -c3 \${ip_list[\$count]} &>/dev/null; echo \$?\`
    if [[ \$ping_status -eq 0 ]]
    then
        ping_status=1
    else
        ping_status=0
    fi
    echo "node_ping_status{network=\"\${int_name[\$count]}\",ip=\"\${ip_list[\$count]}\"}" \$ping_status
    count=\$(( \$count + 1 ))
done
EOL

chmod a+x ${dir_size_script_path}
chmod a+x ${ping_test_script_path}

echo -e "\n\t***** INFO: Creating a cron job *****"

cron_file_path="/etc/crontab"
cat << EOL >> ${cron_file_path}

* * * * * root /etc/node_exporter/dir_size.sh > /etc/node_exporter/textfile_collector/dir_size.prom
* * * * * root /etc/node_exporter/ping_test.sh > /etc/node_exporter/textfile_collector/ping_test.prom

EOL

echo -e "\n\t***** INFO: Granting access to port 9100 *****"

firewall-cmd --zone=public --permanent --add-port=9100/tcp
firewall-cmd --reload

echo -e "\n\t***** INFO: Creating node_exporter service *****"

node_exporter_service_path="/etc/systemd/system/node_exporter.service"
cat << EOL > ${node_exporter_service_path}
[Unit]
Description=NodeExporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter --collector.textfile.directory=/etc/node_exporter/textfile_collector

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl start node_exporter
systemctl enable node_exporter

echo -e "\n***** SUCCESS!! *****"
echo "Node exporter is successfully installed and configured on the system."
echo "Metrics are ready to be scraped from http://localhost:9100/metrics"
