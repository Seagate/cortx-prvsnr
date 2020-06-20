{% import_yaml 'components/defaults.yaml' as defaults %}
Add Saltsatck repo:
  pkgrepo.managed:
    - name: {{ defaults.base_repos.saltstack_repo.id }}
    - humanname: saltstack
    - baseurl: {{ defaults.base_repos.saltstack_repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.base_repos.saltstack_repo.url }}/SALTSTACK-GPG-KEY.pub
    - priority: 1
