{% if "RedHat" in grains['os'] %}
Install sos:
  pkg.installed:
    - name: sos
{% endif %}