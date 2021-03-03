# Enable glusterfsd.service:
#   service.running:
#     - name: glusterfsd.service
#     - enable: True

Enable glusterfssharedstorage.service:
  service.enabled:
    - name: glusterfssharedstorage.service
