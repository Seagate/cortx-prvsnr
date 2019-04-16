include:
  - components.s3s3server.build_ssl_cert_rpms.prepare
  - components.s3s3server.build_ssl_cert_rpms.install
  - components.s3s3server.build_ssl_cert_rpms.config
  - components.s3s3server.build_ssl_cert_rpms.housekeeping
  - components.s3s3server.build_ssl_cert_rpms.sanity_check

# install_s3server_certs:
#   pkg.installed:
#     - sources: {{ rpm_sources_dir }}/stx-s3-certs
#       -
# remove_stx-s3-certs:
#   file.absent:
#     - name: {{ rpm_sources_dir }}/{{ s3_certs_src }}
#     - require:
#       - create archive
