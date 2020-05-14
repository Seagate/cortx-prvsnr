{% if "RedHat" in grains['os'] %}
Remove sos:
  pkg.removed:
    - name: sosreport
{% endif %}