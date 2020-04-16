{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Stage - Post Install S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/s3server/conf/setup.yaml', 's3server:post_install')
{% endif %}

Encrypt ldap password:
  cmd.run:
    - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ salt['lyveutil.decrypt'](pillar['openldap']['iam_admin']['secret'],'openldap') }} -p /opt/seagate/auth/resources/authserver.properties
    - onlyif: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
    - watch_in:
      - service: s3authserver

s3authserver:
  service.running:
    - init_delay: 2


Append /etc/hosts:
  file.line:
    - name: /etc/hosts
    - content: {{ pillar['cluster']['cluster_ip'] }}  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
    - location : end
    - mode: insert


Add slapd.conf to /etc/rsyslog.d:
  file.managed:
    - name: /etc/rsyslog.d/slapd.conf
    - source: /opt/seagate/s3/install/ldap/rsyslog.d/slapdlog.conf
    - makedirs: True
    - keep_source: True
