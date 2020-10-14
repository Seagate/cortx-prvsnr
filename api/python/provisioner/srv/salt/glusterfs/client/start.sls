# Enable glusterfsd.service:
#   service.running:
#     - name: glusterfsd.service
#     - enable: True

Enable glusterfssharedstorage.service:
  service.enabled:
    - name: glusterfssharedstorage.service

Enable sync-saltdata.service:
  service.enabled:
    - name: sync-saltdata.service
