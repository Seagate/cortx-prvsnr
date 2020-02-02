Configure Kibana:
  file.managed:
    - name: /etc/kibana/kibana.yml
    - source: salt://components/misc_pkgs/kibana/files/kibana.yml
