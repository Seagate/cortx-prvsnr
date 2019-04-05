{% import_yaml 'components/defaults.yaml' as defaults %}

add_s3server_repo:
  pkgrepo.managed:
    - name: {{ defaults.s3server.repo.id }}
    - enabled: True
    - baseurl: {{ defaults.s3server.repo.url }}
    - gpgcheck: 0

{% if salt['grains.get']('host').startswith('cmu') %}
# S3 installation start
add_s3server_uploads_repo:
  pkgrepo.managed:
    - name: {{ defaults.s3server.uploads_repo.id }}
    - enabled: True
    - humanname: s3server_uploads
    - baseurl: {{ defaults.s3server.uploads_repo.url }}
    - gpgcheck: 0

install_s3server_uploads:
  pkg.installed:
    - pkgs:
      - python34-jmespath
      - python34-botocore
      - python34-s3transfer
      - python34-boto3
      - python34-xmltodict
    - require:
      - pkgrepo: add_s3server_uploads_repo

install_s3s3iamcli:
  pkg.installed:
    - pkgs:
      - s3iamcli
      # is this required in PROD?
      # - s3iamcli-devel
      # - s3server-debuginfo

{% else %}

install_s3server:
  pkg.installed:
    - pkgs:
      - s3server
    - require:
      - pkgrepo: add_s3server_repo

{% endif %}

# modify_s3config_file:
#   file.replace:
#     - name: /opt/seagate/s3/conf/s3config.yaml
#     - pattern: "S3_ENABLE_STATS:.+false"
#     - repl: "S3_ENABLE_STATS: true"
#     - require:
#       - install_s3server
# S3 installation end
