copy_cluster_yaml:
  file.copy:
    - name: /etc/csm/cluster.yaml
    - source: salt://csm/files/etc/csm/cluster.yaml.template
    - force: True
    - makedirs: True

# Append list using command: cat /etc/hosts |grep -Poe '\w+-m10$'

# modify_cluster_yaml:

# Modify port in /etc/grafana/grafana.ini
# /etc/grafana/grafana.ini
# modify line: ;http_port = 3000

execute_csm_init:
  cmd.run:
    - name: /opt/seagate/csm/csm_init config -f -s -l
    - onlyif: test -f /opt/seagate/csm/csm_init
