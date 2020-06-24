{% from "components/map.jinja" import reporef with context %}

Add Saltsatck repo:
  pkgrepo.managed:
    - name: {{ reporef.base_repos.saltstack_repo.id }}
    - humanname: saltstack
    - baseurl: {{ reporef.base_repos.saltstack_repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ reporef.base_repos.saltstack_repo.url }}/SALTSTACK-GPG-KEY.pub
    - priority: 1
