Sync data:
  module.run:
    - saltutil.clear_cache: []
    - saltutil.sync_all: []
    - saltutil.refresh_grains: []
    - saltutil.refresh_modules: []
    - saltutil.refresh_pillar: []

{% import_yaml 'components/defaults.yaml' as defaults %}

{% if "RedHat" in grains['os'] %}

# Add repo for HA
Add uploads_rhel yum repo:
  pkgrepo.managed:
    - name: {{ defaults.uploads_rhel.repo.id }}
    - enabled: True
    - humanname: uploads_rhel
    - baseurl: {{ defaults.uploads_rhel.repo.url }}
    - gpgcheck: 0

{% else %}
# Adding repos here are redundent thing.
# These repos get added in prereq-script, setup-provisioner
#TODO Remove redundency
 
cleanup_yum_repos_dir:
  cmd.run:
    - name: rm -rf /etc/yum.repos.d/*.repo
    - if: test -f /etc/yum.repos.d/CentOS-Base.repo

Reset EPEL:
  cmd.run:
    - name: rm -rf /etc/yum.repos.d/epel.repo.*
    - if: test -f /etc/yum.repos.d/epel.repo.rpmsave

Configure yum:
  file.managed:
    - name: /etc/yum.conf
    - source: salt://components/system/files/etc/yum.conf


{% for repo in defaults.base_repos.centos_repos %}
add_{{repo.id}}_repo:
  pkgrepo.managed:
    - name: {{ repo.id }}
    - humanname: {{ repo.id }}
    - baseurl: {{ repo.url }}
    - gpgcheck: 0
{% endfor %}

add_epel_repo:
  pkgrepo.managed:
    - name: {{ defaults.base_repos.epel_repo.id }}
    - humanname: epel
    - baseurl: {{ defaults.base_repos.epel_repo.url }}
    - gpgcheck: 0

add_saltsatck_repo:
  pkgrepo.managed:
    - name: {{ defaults.base_repos.saltstack_repo.id }}
    - humanname: saltstack
    - baseurl: {{ defaults.base_repos.saltstack_repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.base_repos.saltstack_repo.url }}/SALTSTACK-GPG-KEY.pub

Add commons yum repo:
  pkgrepo.managed:
    - name: {{ defaults.commons.repo.id }}
    - enabled: True
    - humanname: commons
    - baseurl: {{ defaults.commons.repo.url }}
    - gpgcheck: 0

{% endif %}

clean_yum_local:
  cmd.run:
    - name: yum clean all

clean_yum_cache:
  cmd.run:
    - name: rm -rf /var/cache/yum

