{% if "RedHat" in grains['os'] %}
Remove sos:
  pkg.removed:
    - name: sos

Remove SOS report directory:
  file.absent:
    - name: /opt/seagate/os

{% else %}
No HA cleanup for CSM:
  test.show_notification:
      - text: "SOS is not required for Non RedHat systems, skipping.."

{% endif %}
