{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_dir = defaults.tmp_dir + "/s3certs" %}

Delete dir rpm:
  file.absent:
    - name: {{ rpm_dir }}

Remove rpmbuild:
  pkg.purged:
    - name: rpm-build
