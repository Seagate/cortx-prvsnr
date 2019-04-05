{% if ((salt['grains.get']('host').startswith('cmu')) and (not salt['grains.get']('productname').lower().startswith('virtual'))) %}
# This formula is unnecessary and should never be executed.

hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
    - user: root
    - group: root

{% endif %}
