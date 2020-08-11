provisioner_package_installed:
  pkg.installed:
    - pkgs:
      - cortx-prvsnr: latest
      # TODO EOS-11551 enable later
      # - python36-cortx-prvsnr: latest
    - refresh: True
