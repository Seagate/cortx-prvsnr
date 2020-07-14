Render ha input params template:
  file.managed:
    - name: /opt/seagate/cortx/ha/conf/build-ees-ha-args.yaml
    - source: salt://components/ha/ees_ha/files/ha-params.tmpl
    - template: jinja
    - mode: 444
    - makedirs: True
