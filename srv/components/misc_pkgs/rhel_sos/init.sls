{% if "RedHat" in grains['os'] %}
Install sos:
  pkg.installed:
    - name: sosreport
{% endif %}