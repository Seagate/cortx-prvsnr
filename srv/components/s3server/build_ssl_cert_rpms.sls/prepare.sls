{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_sources_dir = defaults.tmp_dir + "/s3certs/rpmbuild/SOURCES/" %}
{% set s3_certs_src = "stx-s3-certs-" + defaults.s3server.config.S3_VERSION + '-' + defaults.s3server.config.DEPLOY_TAG %}

copy_s3_utils:
  file.recurse:
    - name: /opt/seagate/s3server/
    - source: salt://components/s3server/files/
    - user: root
    - group: root
    - file_mode: 750
    - dir_mode: 640
    - keep_source: False
    - clean: True
    - replace: True

create_rpm_sources_dir:
  file.directory:
    - name: {{ rpm_sources_dir }}
    - user: root
    - group: root
    - dir_mode: 640
    - file_mode: 750
    - recurse:
      - user
      - group
      - mode
    - clean: True
    - makedirs: True

ensure_s3_certs_dir:
  file.directory:
    - name: {{ rpm_sources_dir }}/{{ s3_certs_src }}
    - user: root
    - group: root
    - dir_mode: 640
    - file_mode: 750
    - recurse:
      - user
      - group
      - mode
