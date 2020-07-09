hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1     localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1           localhost localhost.localdomain localhost6 localhost6.localdomain6
        -------------------------------------------------------------------------------
        {%- for node in pillar['cluster']['node_list'] %}
        {%- if pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr'] %}
        {{ pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr'] }}   {{ node -}}
        {%- else %}
        {%- for srvnode, ip_data in salt['mine.get'](node, 'node_ip_addrs') | dictsort() %}
        {{ ip_data[pillar['cluster'][srvnode]['network']['data_nw']['iface'][1]][0] }}   {{ srvnode -}}
        {% endfor -%}
        {% endif -%}
        {% endfor %}
    - user: root
    - group: root
