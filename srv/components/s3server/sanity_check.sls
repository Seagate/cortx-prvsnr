Verify slapd port listens:
  cmd.run:
    - name: netstat -plnt | grep :$(grep -Po "(?<=ldapPort=).*" /opt/seagate/auth/resources/authserver.properties)

#Verify slapd SSL port listens:
#  cmd.run:
#    - name: netstat -plnt | grep :$(grep -Po "(?<=ldapSSLPort=).*" /opt/seagate/auth/resources/authserver.properties)

Verify HTTP port listens:
  cmd.run:
    - name: netstat -plnt | grep :$(grep -Po "(?<=httpPort=).*" /opt/seagate/auth/resources/authserver.properties)

# Verify HTTPS port listens:
#   cmd.run:
#     - name: netstat -plnt | grep :$(grep -Po "(?<=httpsPort=).*" /opt/seagate/auth/resources/authserver.properties)
