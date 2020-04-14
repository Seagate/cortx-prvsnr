# Log rotate teardown start
# logrotate.d
# Remove logrotate directory:
#   file.absent:
#     - name: /etc/logrotate.d

# # general settings
# Remove generic logrotate config:
#   file.absent:
#     - name: /etc/logrotate.conf
#     - source: salt://components/system/files/etc/logrotate.conf

# Remove logrotate
# Remove logrotate package:
#   pkg.purged:
#     - name: logrotate

Delete logrotate checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.logrotate