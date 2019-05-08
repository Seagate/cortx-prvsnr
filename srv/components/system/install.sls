# update_yum_repos:
#   module.run:
#     - pkg.update:

install_base_packages:
  pkg.installed:
    - pkgs:
      - vim-enhanced
      - jq
      # - tmux
