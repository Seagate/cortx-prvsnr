include:
# Clients
  - components.s3clients.awscli.teardown
  - components.s3clients.s3cmd.teardown


Remove S3 client certs:
  pkg.removed:
    - name: stx-s3-client-certs

Remove client cert rpm:
  file.absent:
    - name: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

Remove S3 iamcli:
  pkg.removed:
    - pkgs:
      - s3iamcli
#       # - s3iamcli-devel
#       # - s3server-debuginfo


Delete s3clients checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.s3clients

