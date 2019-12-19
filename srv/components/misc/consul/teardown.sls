Stop consul:
  cmd.run:
    - name: /opt/consul/consul leave

{% if salt['ps.pgrep']('consul') -%}
Kill m0d process:
  module.run:
    - ps.pkill:
      - pattern: consul
      - signal: 9
{%- endif %}

Remove Consul:
  file.absent:
    - name: /opt/consul

Remove consul from bash_profile:
  file.blockreplace:
    - name: ~/.bashrc
    - marker_start: '# DO NOT EDIT: Consul binaries'
    - marker_end: '# DO NOT EDIT: End'
    - content: ''

Source bash_profile for consul cleanup:
  cmd.run:
    - name: source ~/.bashrc
