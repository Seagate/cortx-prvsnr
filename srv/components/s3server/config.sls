# modify_s3config_file:
#   file.replace:
#     - name: /opt/seagate/s3/conf/s3config.yaml
#     - pattern: "S3_ENABLE_STATS:.+false"
#     - repl: "S3_ENABLE_STATS: true"
#     - require:
#       - install_s3server
# S3 installation end

Restart S3AuthServer:
  service.running:
    - name: s3authserver

Encrypt ldap password:
  cmd.run:
    - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ pillar['openldap']['ldapiamadminpasswd'] }} -p /opt/seagate/auth/resources/authserver.properties
    - unless: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
    - watch_in:
      - service: Restart S3AuthServer
