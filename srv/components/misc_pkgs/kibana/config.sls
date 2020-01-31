Configure Kibana:
  file.managed:
    - name: /etc/kibana/kibana.yml
    - source: salt://components/misc/kibana/files/kibana.yml
