Remove Packages:
  pkg.purged:
    - pkgs:
      - openssl-libs
      - openssl
      - rpm-build
      - java-1.8.0-openjdk-headless.x86_64

Remove certs directory:
  file.absent:
    - names:
      - /etc/ssl/stx-s3/s3auth
      - /etc/ssl/stx-s3/s3

Remove certs user:
  user.absent:
    - name: certs

Remove certs group:
  group.absent:
    - name: certs

