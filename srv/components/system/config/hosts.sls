hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1     localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1           localhost localhost.localdomain localhost6 localhost6.localdomain6
        -------------------------------------------------------------------------------
        {% for node in pillar['cluster']['node_list'] %}
        {% set pvt_nw = pillar['cluster']['pvt_data_nw_addr'] %}
        {% set pvt_ip = ("{0}.{1}").format('.'.join(pvt_nw.split('.')[:3]), node.split('-')[1]) %}
        {{ pvt_ip }}   {{ node }}
        {% endfor %}
        
    - user: root
    - group: root
