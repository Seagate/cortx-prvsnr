Verify slapd port listens:
  cmd.run:
    - name: netstat -plnt | grep :$(grep -Po "(?<=ldapPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

#Verify slapd SSL port listens:
#  cmd.run:
#    - name: netstat -plnt | grep :$(grep -Po "(?<=ldapSSLPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

Verify HTTP port listens:
  cmd.run:
    - name: netstat -plnt | grep :$(grep -Po "(?<=httpPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

# Verify HTTPS port listens:
#   cmd.run:
#     - name: netstat -plnt | grep :$(grep -Po "(?<=httpsPort=).*" /opt/seagate/cortx/auth/resources/authserver.properties)

# Test section is missing in /opt/seagate/cortx/s3/conf/setup.yaml
# Stage - Test S3:
#   cmd.run:
#     - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/s3/conf/setup.yaml', 's3server:test')
