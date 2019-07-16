#TODO: Commenting due to a known issue.
#Update s3 config file with pillar data:
#  module.run:
#    - eos.conf_update:
#      - name: /opt/seagate/s3/conf/s3config.yaml
#      - ref_pillar: s3_pillar_data
#      - type: YAML
#      - backup: True

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
    - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ pillar['openldap']['iam_admin_passwd'] }} -p /opt/seagate/auth/resources/authserver.properties
    - onlyif: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
    - watch_in:
      - service: s3authserver

s3authserver:
  service.running:
    - enable: True
    - init_delay: 2

Open http port for s3server:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: ACCEPT
    - protocol: tcp
    - match: tcp
    - dport: 80
    - family: ipv4
    - save: True

Open https port for s3server:
  iptables.insert:
    - position: 1
    - table: filter
    - chain: INPUT
    - jump: ACCEPT
    - protocol: tcp
    - match: tcp
    - dport: 443
    - family: ipv4
    - save: True

# Append /etc/hosts:
#   file.line:
#     - name: /etc/hosts
#     - content: {{ grains['ip_interfaces']['data0'][0] }}  s3.cloud.seagate.com iam.cloud.seagate.com sts.cloud.seagate.com
#     - location: end
#     - mode: ensure
