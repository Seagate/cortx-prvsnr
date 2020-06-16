Copy setup.yaml to /opt/seagate/health_view/conf:
  file.managed:
    - name: /opt/seagate/health_view/conf/setup.yaml
    - source: salt://components/sspl/health_view/files/setup.yaml
    - makedirs: True
