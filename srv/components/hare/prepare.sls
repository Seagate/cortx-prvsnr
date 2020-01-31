{% import_yaml 'components/defaults.yaml' as defaults %}

Add hare yum repo:
  pkgrepo.managed:
    - name: {{ defaults.hare.repo.id }}
    - enabled: True
    - humanname: hare
    - baseurl: {{ defaults.hare.repo.url }}
    - gpgcheck: 0

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Prepare cluster yaml:
  file.managed:
    - name: /var/lib/hare/cluster.yaml
    - source: salt://components/hare/files/cluster.cdf.tmpl
    - template: jinja
    - mode: 444
    - makedirs: True
{% endif %}
