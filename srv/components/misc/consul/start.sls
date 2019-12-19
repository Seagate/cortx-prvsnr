Start Consul:
  cmd.run:
    - name: nohup /opt/consul/consul agent -dev </dev/null >/dev/null 2>&1 &
