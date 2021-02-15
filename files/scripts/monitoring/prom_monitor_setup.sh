#!/bin/bash

tar1=
tar2=

usage()
{
	echo "\
Usage:
For dual-node cluster :
Required arguments:
	-t1  <Target_1_IP>		- IP address of node 1 to be monitored.
	-t2  <Target_2_IP>		- IP address of node 2 to be monitored.
Optional arguments:
	-h|--help   	brief info about script

---------------- Sample command ---------------------
$ sh prom_monitor_setup.sh -t1 10.230.249.167 -t2 10.230.240.110

"
}

count=0

while [[ $# -gt 0 ]]; 
do
	case $1 in 
		-h|--help) usage; exit 0
		;;
		-t1)
			[ -z "$2" ] && echo "Error: Target 1 IP address not provided" && exit 1;
			tar1="$2"
			count=$((count + 1))
			shift 2
		;;
		-t2)
			[ -z "$2" ] && echo "Error: Target 2 IP address not provided" && exit 1;
			tar2="$2"
			count=$((count + 1))
			shift 2
		;;
		*) 
			echo "Invalid option $1"; usage; exit 1;
		;;
	esac
done

if [[ $count -ne 2 ]]
then
	echo "Error: Insufficient input provided"
	usage
	exit 1
fi

echo -e "\n\t***** INFO: Installing Prometheus *****"

useradd --no-create-home --shell /bin/false prometheus
mkdir /etc/prometheus
mkdir /var/lib/prometheus
chown prometheus:prometheus /etc/prometheus
chown prometheus:prometheus /var/lib/prometheus

curl -LO https://github.com/prometheus/prometheus/releases/download/v2.22.0-rc.0/prometheus-2.22.0-rc.0.linux-amd64.tar.gz
tar -xvf prometheus-2.22.0-rc.0.linux-amd64.tar.gz
mv prometheus-2.22.0-rc.0.linux-amd64 prometheus-files
rm -rf prometheus-2.22.0-rc.0.linux-amd64.tar.gz

cp prometheus-files/prometheus /usr/local/bin/
cp prometheus-files/promtool /usr/local/bin/
chown prometheus:prometheus /usr/local/bin/prometheus
chown prometheus:prometheus /usr/local/bin/promtool

cp -r prometheus-files/consoles /etc/prometheus
cp -r prometheus-files/console_libraries /etc/prometheus
chown -R prometheus:prometheus /etc/prometheus/consoles
chown -R prometheus:prometheus /etc/prometheus/console_libraries

echo -e "\n\t***** INFO: Granting access to port 9090 *****"

firewall-cmd --zone=public --permanent --add-port=9090/tcp
firewall-cmd --reload

prom_config_file_path="/etc/prometheus/prometheus.yml"
cat << EOL > ${prom_config_file_path}
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

scrape_configs:
  - job_name: 'node_1'
    scrape_interval: 5s
    static_configs:
      - targets: ['$tar1:9100']

  - job_name: 'node_2'
    scrape_interval: 5s
    static_configs:
      - targets: ['$tar2:9100']

EOL

chown prometheus:prometheus /etc/prometheus/prometheus.yml

echo -e "\n\t***** INFO: Creating prometheus service *****"

prom_service_file_path='/etc/systemd/system/prometheus.service'
cat << EOL > ${prom_service_file_path}
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl start prometheus
systemctl enable prometheus

echo -e "\n***** SUCCESS!! *****"
echo "Prometheus monitor is successfully installed and configured."
echo "The metrics of the target nodes are available at http://localhost:9090/metrics"
echo "To perform query operations on the metrics, please visit http://localhost:9090/graph"

# ------------------------ Setup Grafana Server -----------------------------------

echo -e "\n\t***** INFO: Installing Grafana-Server *****"

wget https://dl.grafana.com/oss/release/grafana-7.2.0-1.x86_64.rpm
yum install -y grafana-7.2.0-1.x86_64.rpm

echo -e "\n\t***** INFO: Granting access to port 3000 *****"
firewall-cmd --zone=public --permanent --add-port=3000/tcp
firewall-cmd --reload

systemctl daemon-reload
systemctl start grafana-server
systemctl enable grafana-server

echo -e "\n***** SUCCESS!! *****"
echo "Grafana server is successfully installed and configured on http://localhost:3000"
