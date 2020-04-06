Append /etc/hosts:
  file.line:
    - name: /etc/hosts
    - mode: ensure
    - content: {{ pillar['s3clients']['s3server']['ip'] }}  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
    - after: "::1.+localhost.+"
