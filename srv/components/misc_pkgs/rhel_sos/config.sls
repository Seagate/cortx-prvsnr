Copy setup.yaml to /opt/seagate/os/conf:
  file.managed:
    - name: /opt/seagate/os/conf/setup.yaml
    - source: salt://components/misc_pkgs/rhel_sos/files/setup.yaml
    - makedirs: True
