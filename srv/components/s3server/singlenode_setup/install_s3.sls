{% import_yaml 'components/defaults.yaml' as defaults %}

install_s3_dependencies:
  cmd.run:
    - name: /opt/seagate/
    - cwd: {{ rpm_sources_dir }}/{{ s3_certs_src }}


install_s3server_uploads:
  pkg.installed:
    - pkgs:
      - python34-jmespath
      - python34-botocore
      - python34-s3transfer
      - python34-boto3
      - python34-xmltodict

install_s3server:
  pkg.installed:
    - name: s3server

s3authserver:
  service.running:
    - enable: True
