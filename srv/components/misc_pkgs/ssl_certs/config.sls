Place certs at temp location:
  file.managed:
    - name: /etc/ssl/stx/stx.pem
    - source: salt://components/misc_pkgs/ssl_certs/files/stx.pem
    - force: true
    - makedirs: True

Clean temp:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/ssl/certs
