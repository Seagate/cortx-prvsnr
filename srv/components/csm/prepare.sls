{% import_yaml 'components/defaults.yaml' as defaults %}

Add CSM uploads repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.uploads_repo.id }}
    - enabled: True
    - humanname: csm_uploads
    - baseurl: {{ defaults.csm.uploads_repo.url }}
    - gpgcheck: 0

Add CSM repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.repo.id }}
    - enabled: True
    - humanname: csm
    - baseurl: {{ defaults.csm.repo.url }}
    - gpgcheck: 0

{% if pillar['cluster']['type'] ==  'ees' %}
Render CSM ha input params template:
  file.managed:
    - name: /var/lib/hare/build-ees-ha-csm-args.yaml
    - source: salt://components/csm/files/ha-params.tmpl
    - template: jinja
    - mode: 444
    - makedirs: True
{% endif %}
