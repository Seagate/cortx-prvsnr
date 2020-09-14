{% set private_ip = pillar["cluster"][grains['id']]["network"]["data_nw"]["pvt_ip_addr"] %}

Set PermitRootLogin:
  file.replace:
    - name: /etc/ssh/sshd_config
    - pattern: ^PermitRootLogin .*
    - repl: PermitRootLogin no
    - append_if_not_found: True


Set private ips root login:
  file.append:
    - name: /etc/ssh/sshd_config
    - text:
      -  Match Address {{ private_ip}}
      -  "    PermitRootLogin yes"

