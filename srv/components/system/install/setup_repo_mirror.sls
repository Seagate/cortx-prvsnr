# To be executed only on CMU
{% if salt['grains.get']('host').startswith('cmu') %}

{% for directory in ("releases", "prvsnr") %}
mount_ci-storage_{{ directory }}:
  mount.mounted:
    - name: /ci-storage/{{ directory }}
    - device: ci-storage.mero.colo.seagate.com:/mnt/bigstorage/{{ directory }}
    - fstype: nfs
    - mkmnt: True
    - opts: ro
    - mount: True
{% endfor %}

# /etc/sysconfig/darkhttpd:
#   file.managed:
#     - contents: |
#         DARKHTTPD_ROOT="/ci-storage"
#         DARKHTTPD_FLAGS="--log /var/log/darkhttpd.log --uid root --gid root --addr {{ salt['grains.get']('ipv4:2') }}"
#         MIMETYPES="--mimetypes /etc/mime.types"
#
# darkhttpd:
#   pkg.installed: []
#   service.running:
#     - watch:
#       - file: /etc/sysconfig/darkhttpd

{% endif %}
