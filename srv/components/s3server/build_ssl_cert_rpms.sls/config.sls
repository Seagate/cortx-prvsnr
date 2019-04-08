{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_sources_dir = defaults.tmp_dir + "/s3certs/rpmbuild/SOURCES/" %}
{% set s3_certs_src = "stx-s3-certs-" + defaults.s3server.config.S3_VERSION + '-' + defaults.s3server.config.DEPLOY_TAG %}

generate_s3_certs:
  cmd.run:
    - name: /opt/seagate/s3server/ssl/generate_certificate.sh -f domain_input.conf
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

build_s3server_certs_rpm:
  cmd.run:
    - name: rpmbuild -ba --define "_s3_certs_version {{ defaults.s3server.config.S3_VERSION }}" \
         --define "_s3_certs_src {{ s3_certs_src }}" \
         --define "_s3_domain_tag {{ defaults.s3server.config.S3_DOMAIN }}" \
         --define "_s3_deploy_tag {{ defaults.s3server.config.DEPLOY_TAG }}" \
        /opt/seagate/s3server/s3certs/s3certs.spec
    - cwd: {{ rpm_sources_dir }}
    - watch_in:
      - remove_rpmbuild

build_s3client_certs_rpm:
  cmd.run:
    - name: rpmbuild -ba --define "_s3_certs_version {{ defaults.s3server.config.S3_VERSION }}" \
         --define "_s3_certs_src {{ s3_certs_src }}" \
         --define "_s3_domain_tag {{ defaults.s3server.config.S3_DOMAIN }}" \
         --define "_s3_deploy_tag {{ defaults.s3server.config.DEPLOY_TAG }}" \
         /opt/seagate/s3server/s3certs/s3clientcerts.spec
    - cwd: {{ rpm_sources_dir }}
    - watch_in:
      - remove_rpmbuild
