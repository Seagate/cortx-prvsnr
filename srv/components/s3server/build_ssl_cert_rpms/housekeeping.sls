{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_sources_dir = defaults.tmp_dir + "/s3certs/rpmbuild/SOURCES/" %}

delete_rpm_sources_dir:
  file.absent:
    - name: {{ rpm_sources_dir }}

remove_rpmbuild:
  pkg.purged:
    - name: rpm-build
