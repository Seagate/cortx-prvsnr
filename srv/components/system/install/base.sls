{% import_yaml 'components/defaults.yaml' as defaults %}

cleanup_yum_repos_dir:
  cmd.run:
    - name: rm -rf /etc/yum.repos.d/*.repo
    - if: test -f /etc/yum.repos.d/CentOS-Base.repo

{% for repo in defaults.base_repos.centos_repos %}
add_{{repo.id}}_repo:
  pkgrepo.managed:
    - name: {{ repo.id }}
    - enabled: True
    - humanname: {{ repo.id }}
    - baseurl: {{ repo.url }}
    - gpgcheck: 0
{% endfor %}

add_epel_repo:
  pkgrepo.managed:
    - name: {{ defaults.base_repos.epel_repo.id }}
    - enabled: True
    - humanname: epel
    - baseurl: {{ defaults.base_repos.epel_repo.url }}
    - gpgcheck: 0

add_saltsatck_repo:
  pkgrepo.managed:
    - name: {{ defaults.base_repos.saltsatck_repo.id }}
    - enabled: True
    - humanname: saltstack
    - baseurl: {{ defaults.base_repos.saltsatck_repo.url }}
    - gpgcheck: 0

clean_yum_local:
  cmd.run:
    - name: yum clean all

clean_yum_cache:
  cmd.run:
    - name: rm -rf /var/cache/yum

# update_yum_repos:
#   module.run:
#     - pkg.update:

install_base_packages:
  pkg.installed:
    - pkgs:
      - python2-pip
      # - vi-enhanced
      # - tmux
