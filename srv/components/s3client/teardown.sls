include:
# Clients
  - components.s3client.awscli.teardown
  - components.s3client.s3cmd.teardown


Remove S3 client certs:
  pkg.removed:
    - name: stx-s3-client-certs

Remove S3 iamcli:
  pkg.removed:
    - pkgs:
      - s3iamcli
#       # - s3iamcli-devel
#       # - s3server-debuginfo
