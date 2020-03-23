{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/ssl/certs/stx.pem') %}

Place certs at temp location:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/ssl/certs/stx.pem
    - source: salt://components/misc_pkgs/ssl_certs/files/s3server.pem
    - force: true
    - makedirs: True

{% endif %}

Copy certs to destination:
  file.copy:
    - name: /etc/ssl/stx/stx.pem
    - source: /opt/seagate/eos-prvsnr/generated_configs/ssl/certs/stx.pem
    - force: True
    - makedirs: True
    - user: certs
    - group: certs
    - mode: 440

Clean temp:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/ssl/certs
