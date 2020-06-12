# Disable SSL:
#   file.managed:
#     - name: /etc/python/cert-verification.cfg
#     - contents: |
#         [https]
#         verify=disable
