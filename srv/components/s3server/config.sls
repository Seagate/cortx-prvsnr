{% if pillar["cluster"][grains["id"]]["is_primary"] %}
Stage - Post Install S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:post_install')
{% endif %}

# Update password in authserver.properties:
#   cmd.run:
#     - name: /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh -l {{ salt['lyveutil.decrypt'](pillar['openldap']['iam_admin']['secret'],'openldap') }} -p /opt/seagate/auth/resources/authserver.properties
#     - onlyif: test -f /opt/seagate/auth/scripts/enc_ldap_passwd_in_cfg.sh
#     - watch_in:
#       - service: s3authserver

Stage - Config S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:config')

Stage - Init S3Server:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:init')

Append /etc/hosts:
  file.line:
    - name: /etc/hosts
    - content: {{ pillar['cluster']['cluster_ip'] }}  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
    - location : end
    - mode: insert
