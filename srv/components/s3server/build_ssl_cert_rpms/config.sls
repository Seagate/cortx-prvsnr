{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_root_dir = defaults.tmp_dir + "/s3certs/rpmbuild" %}
{% set rpm_sources_dir = rpm_root_dir + "/SOURCES" %}
{% set s3_certs_src = "stx-s3-certs-" + defaults.s3server.config.S3_VERSION + '-' + defaults.s3server.config.DEPLOY_TAG %}

generate_s3_certs:
  cmd.run:
    - name: /opt/seagate/s3server/ssl/generate_certificate.sh -f domain_input.conf
    - cwd: {{ rpm_sources_dir }}/{{ s3_certs_src }}

copy_s3_certs:
  cmd.run:
    - name: cp -r s3_certs_sandbox/* .
    - cwd: {{ rpm_sources_dir }}/{{ s3_certs_src }}

remove_sandbox:
  file.absent:
    - name: {{rpm_sources_dir}}/{{ s3_certs_src }}/s3_certs_sandbox

create_archive:
  module.run:
    - archive.tar:
      - options: czf
      - tarfile: {{ s3_certs_src }}.tar.gz
      - sources: {{ s3_certs_src }}
      - cwd: {{ rpm_sources_dir }}

build_s3server_certs_rpm:
  cmd.run:
    - name: rpmbuild -ba --define="_s3_certs_version {{ defaults.s3server.config.S3_VERSION }}" --define="_s3_certs_src {{ s3_certs_src }}" --define="_s3_domain_tag {{ defaults.s3server.config.S3_DOMAIN }}" --define="_s3_deploy_tag {{ defaults.s3server.config.DEPLOY_TAG }}" --define="_topdir {{ rpm_root_dir }}" /opt/seagate/s3server/s3certs/s3certs.spec
    - cwd: {{ rpm_sources_dir }}

copy_s3server_certs_rpm:
  cmd.run:
    - name: cp {{ rpm_root_dir }}/RPMS/x86_64/stx-s3-certs-* /opt
    - require:
      - build_s3server_certs_rpm

build_s3client_certs_rpm:
  cmd.run:
    - name: rpmbuild -ba --define="_s3_certs_version {{ defaults.s3server.config.S3_VERSION }}" --define="_s3_certs_src {{ s3_certs_src }}" --define="_s3_domain_tag {{ defaults.s3server.config.S3_DOMAIN }}" --define="_s3_deploy_tag {{ defaults.s3server.config.DEPLOY_TAG }}" --define="_topdir {{ rpm_root_dir }}" /opt/seagate/s3server/s3certs/s3clientcerts.spec
    - cwd: {{ rpm_sources_dir }}

copy_s3server_client_client_rpm:
  cmd.run:
    - name: cp {{ rpm_root_dir }}/RPMS/x86_64/stx-s3-client-certs-* /opt
    - require:
      - build_s3client_certs_rpm
