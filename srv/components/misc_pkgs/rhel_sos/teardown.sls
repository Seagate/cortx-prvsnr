{% if "RedHat" in grains['os'] %}
Remove sos:
  pkg.removed:
    - name: sos

Remove SOS report directory:
  file.absent:
    - name: /opt/seagate/os

{% endif %}
