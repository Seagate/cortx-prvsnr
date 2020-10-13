{%- set private_ip_list = [] -%}
{%- for node in pillar['cluster']['node_list'] -%}
{%- do private_ip_list.append(pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr']) %}
{%- endfor %}
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
      -  Match Address {{ private_ip_list|join(',') }}
      -  "      PermitRootLogin yes"
