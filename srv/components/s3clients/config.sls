Append /etc/hosts:
  file.line:
    - name: /etc/hosts
    - mode: ensure
    - content: {{ pillar['s3clients']['s3server']['ip'] }}  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
    - after: "::1         localhost localhost.localdomain localhost6 localhost6.localdomain6"


# Generate base credentials:
#   cmd.run:
#     - name: /bin/s3iamcli createaccount -n s3user -e s3user@seagate.com --ldapuser {{ pillar['s3clients']['s3server']['iam_admin_user'] }} --ldappasswd {{ pillar['s3clients']['s3server']['iam_admin_passwd'] }}  | tee /opt/seagate/.s3-client-credentials
#     - only_if: test -f /bin/s3iamcli
