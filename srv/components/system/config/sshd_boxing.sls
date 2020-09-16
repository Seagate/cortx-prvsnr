{%- set private_ip_list = [] -%}
{%- for node in (pillar['cluster']['node_list']) -%}
{%- for srvnode, ip_data in salt['mine.get'](node, 'node_ip_addrs') | dictsort() %}
{%- do private_ip_list.append(ip_data[pillar['cluster'][srvnode]['network']['data_nw']['iface'][1]][0]) %}
{%- endfor %}
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
      -  "	PermitRootLogin yes"

