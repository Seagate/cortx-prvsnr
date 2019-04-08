# modify_s3config_file:
#   file.replace:
#     - name: /opt/seagate/s3/conf/s3config.yaml
#     - pattern: "S3_ENABLE_STATS:.+false"
#     - repl: "S3_ENABLE_STATS: true"
#     - require:
#       - install_s3server
# S3 installation end
