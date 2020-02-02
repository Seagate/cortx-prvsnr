{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_sources_dir = defaults.tmp_dir + "/s3certs/rpmbuild/SOURCES/" %}
{% set s3_certs_src = "stx-s3-certs-" + defaults.s3server.config.S3_VERSION + '-' + defaults.s3server.config.DEPLOY_TAG %}

Copy s3 utils:
  file.recurse:
    - name: /opt/seagate/s3server/
    - source: salt://components/misc_pkgs/build_ssl_cert_rpms/files/
    - user: root
    - group: root
    - file_mode: 750
    - dir_mode: 640
    - keep_source: False
    - clean: True
    - replace: True
    - template: jinja

Clean slate:
  file.absent:
    - name: {{ rpm_sources_dir }}

Create rpm sources dir:
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

Ensure s3 certs dir:
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
