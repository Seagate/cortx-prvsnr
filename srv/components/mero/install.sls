{% import_yaml 'components/defaults.yaml' as defaults %}

include:
  - components.system.install.base

# install_kernel:
#   pkg.installed:
#     - sources:
#       - kernel: {{ defaults.kernel_pkg }}

add_lustre_repo:
  pkgrepo.managed:
    - name: {{ defaults.lustre.repo.id }}
    - enabled: True
    - humanname: lustre
    - baseurl: {{ defaults.lustre.repo.url }}
    - gpgcheck: 0

add_mero_repo:
  pkgrepo.managed:
    - name: {{ defaults.mero.repo.id }}
    - enabled: True
    - humanname: mero
    - baseurl: {{ defaults.mero.repo.url }}
    - gpgcheck: 0

install_lustre:
  pkg.installed:
    - pkgs:
      - kmod-lustre-client
      - lustre-client
      # - lustre-client-devel
    - require:
      - pkgrepo: add_lustre_repo


install_mero:
  pkg.installed:
    - pkgs:
      - mero
      # - mero-debuginfo
    - require:
      - pkgrepo: add_mero_repo
      # - pkg: install_kernel
