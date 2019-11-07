#CSM Configuration and Initialization

Copy Cluster Configuration file:
  file.copy:
    - name: /etc/csm/cluster.conf
    - source: /etc/csm/cluster.conf.sample
    - force: True
    - unless: diff /etc/csm/cluster.conf.sample /etc/csm/cluster.conf

Initialize CSM setup:
  cmd.run:
    - name: csm_setup init -f
