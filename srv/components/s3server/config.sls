# modify_s3config_file:
#   file.replace:
#     - name: /opt/seagate/s3/conf/s3config.yaml
#     - pattern: "S3_ENABLE_STATS:.+false"
#     - repl: "S3_ENABLE_STATS: true"
#     - require:
#       - install_s3server
# S3 installation end

Import s3openldap cert to s3authserver.jks:
  cmd.run:
    - name: keytool -import -trustcacerts -keystore /etc/ssl/stx-s3/s3auth/s3authserver.jks -storepass seagate -noprompt -alias ldapcert -file /etc/ssl/stx-s3/openldap/s3openldap.crt
    - onlyif: test -f /etc/ssl/stx-s3/openldap/s3openldap.crt
    - watch_in:
      - service: s3authserver

Import s3server cert to s3authserver.jks:
  cmd.run:
    - name: keytool -import -trustcacerts -keystore /etc/ssl/stx-s3/s3auth/s3authserver.jks -storepass seagate -noprompt -alias s3 -file /etc/ssl/stx-s3/s3/s3server.crt
    - onlyif: test -f /etc/ssl/stx-s3/s3/s3server.crt
    - watch_in:
      - service: s3authserver

Encrypt ldap password:
  cmd.run:
    - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ pillar['openldap']['ldapiamadminpasswd'] }} -p /opt/seagate/auth/resources/authserver.properties
    - onlyif: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
    - watch_in:
      - service: s3authserver

s3authserver:
  service.running:
    - enable: True
    - init_delay: 2
