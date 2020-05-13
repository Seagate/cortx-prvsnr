hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1     localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1           localhost localhost.localdomain localhost6 localhost6.localdomain6
        -------------------------------------------------------------------------------
        {% for node in pillar['cluster']['node_list'] %}
        {{ pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr'] }}   {{ node }}
        {% endfor %}

    - user: root
    - group: root
