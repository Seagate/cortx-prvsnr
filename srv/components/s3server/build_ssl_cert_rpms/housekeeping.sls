{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_dir = defaults.tmp_dir + "/s3certs" %}

delete_rpm_dir:
  file.absent:
    - name: {{ rpm_dir }}

remove_rpmbuild:
  pkg.purged:
    - name: rpm-build
