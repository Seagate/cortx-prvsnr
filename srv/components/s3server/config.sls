Encrypt ldap password:
  cmd.run:
    - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ pillar['openldap']['iam_admin_passwd'] }} -p /opt/seagate/auth/resources/authserver.properties
    - onlyif: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
    - watch_in:
      - service: s3authserver

s3authserver:
  service.running:
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

Add slapd.conf to /etc/rsyslog.d:
  file.managed:
    - name: /etc/rsyslog.d/slapd.conf
    - source: /opt/seagate/s3/install/ldap/rsyslog.d/slapdlog.conf
    - makedirs: True
    - keep_source: True
