{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_root_dir = defaults.tmp_dir + "/s3certs/rpmbuild" %}
{% set rpm_sources_dir = rpm_root_dir + "/SOURCES" %}

Remove Packages:
  pkg.purged:
    - pkgs:
#      - openssl-libs       # Removing this breaks yum, ssh. Hence don't uncomment.
#      - openssl            # Removing this breaks yum, ssh. Hence don't uncomment.
      - rpm-build
      - java-1.8.0-openjdk-headless.x86_64

Remove certs:
  file.absent:
    - names:
      - {{ rpm_sources_dir }}
      - /opt/seagate/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
      - /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm
