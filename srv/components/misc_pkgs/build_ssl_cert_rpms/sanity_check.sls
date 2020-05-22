# Ensure stx cert rpms are copied on non primary node
sanity check:
  cmd.run:
    - name: test -f /opt/seagate/stx-s3-certs-*.rpm && test -f /opt/seagate/stx-s3-client-certs-*.rpm
