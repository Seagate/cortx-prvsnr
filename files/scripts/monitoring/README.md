# Steps to install and configure prometheus and grafana server to monitor a 2 node system

1. Run the *node_exporter_setup.sh* script on both the nodes to be monitored.  
   - Metrics are ready to be scraped from `http://localhost:9100/metrics` of each system.  
   - Use **-h** argument to know about how to run this script.  

2. Setup the prometheus server on some other node/vm by running the *prom_monitor_setup.sh* script.
   - The metrics of both the target nodes will be available at `http://localhost:9090/metrics` on the monitor system.
   - Use **-h** argument to know about how to run this script.
   - To perform query operations on the metrics, please visit `http://localhost:9090/graph`.

3. Grafana server will be up and running on port 3000 of the monitor system.  

4. Visit `http://localhost:3000` on the monitor system to open grafana dashboard.  
   - Login with **admin/admin** as default credentials and change the password accordingly.  
   - While adding data source select prometheus and provide url as `http://<IP-OF-MONITOR-SYSTEM>:9090/`.
   - Go to manage dashboard section and import a dashboard having id as [1860](https://grafana.com/grafana/dashboards/1860) and select datasource as prometheus.
   - The dashboard is ready with the default view. You can customize the dashboard view by adding new panels as per the need.

5. To know more about prometheus, node_exporter and grafana, please refer to [prometheus.io](https://prometheus.io/) and [grafana docs](https://grafana.com/docs/grafana/latest/getting-started/).
