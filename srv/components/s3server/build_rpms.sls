{% import_yaml 'defaults.yaml' as defaults %}
{% set DEPLOY_TAG = "s3dev" %}
{% set S3_VERSION = "s3ver" %}
{% set S3_DOMAIN = "s3.seagate.com" %}
{% set rpm_sources_dir = defaults.tmp_dir + "/rpmbuild/SOURCES/" %}
{% set s3_certs_src = "stx-s3-certs-" + S3_VERSION + DEPLOY_TAG %}

ensure_rpm_sources_dir:
  file.directory:
    - name: {{ rpm_sources_dir }}
    - user: root
    - group: root
    - dir_mode: 750
    - file_mode: 640
    - recurse:
      - user
      - group
      - mode

remove_stx-s3-certs:
  file.absent:
    - name: {{ rpm_sources_dir }}/stx-s3-certs*
    - require:
      - ensure_rpm_sources_dir


copy_s3_utils:
  file.recurse:
    - name: /opt/salt/s3server/s3certs
    - source: salt://eos/install/s3server/s3certs
    - user: root
    - group: root
    - file_mode: 640
    - dir_mode: 750

ensure_s3_certs dir:
  file.directory:
    - name: {{ rpm_sources_dir }}/{{ s3_certs_src }}
    - user: root
    - group: root
    - dir_mode: 750
    - file_mode: 640
    - recurse:
      - user
      - group
      - mode

generate_s3_certs:
  cmd.run:
    - name: /opt/salt/s3server/s3certs/ssl/generate_certificate.sh
    - cwd: {{ rpm_sources_dir }}/{{ s3_certs_src }}
    - require:
      - copy_s3_utils
      - ensure_s3_certs_dir

copy_s3_certs:
  file.copy:
    - name: {{ rpm_sources_dir }}/{{ s3_certs_src }}
    - source: {{ rpm_sources_dir }}/{{ s3_certs_src }}/s3_certs_sandbox

create_archive:
  module.run:
    - name: archive.tar
    - options: cjf
    - tarfile: {{ s3_certs_src }}.tar.gz
    - sources: {{ s3_certs_src }}
    - cwd: {{ rpm_sources_dir }}

remove_stx-s3-certs:
  file.absent:
    - name: {{ rpm_sources_dir }}/{{ s3_certs_src }}
    - require:
      - create archive

build_s3server_certs_rpm:
  cmd.run:
    - name: rpmbuild -ba --define "_s3_certs_version {{ S3_VERSION }}" \
         --define "_s3_certs_src {{ s3_certs_src }}" \
         --define "_s3_domain_tag {{ S3_DOMAIN }}" \
         --define "_s3_deploy_tag {{ DEPLOY_TAG }}" /opt/salt/s3server/s3certs/s3certs.spec
    - cwd: {{ rpm_sources_dir }}

build_s3client_certs_rpm:
  cmd.run:
    - name: rpmbuild -ba --define "_s3_certs_version {{ S3_VERSION }}" \
         --define "_s3_certs_src {{ s3_certs_src }}" \
         --define "_s3_domain_tag {{ S3_DOMAIN }}" \
         --define "_s3_deploy_tag {{ DEPLOY_TAG }}" /opt/salt/s3server/s3certs/s3clientcerts.spec
    - cwd: {{ rpm_sources_dir }}
