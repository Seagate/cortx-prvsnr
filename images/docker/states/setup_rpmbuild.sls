setup_rpmbuild:
  pkg.installed:
    - pkgs:
      - git
      - python36
      - rpm-build
      - yum-utils
      - python3-devel
