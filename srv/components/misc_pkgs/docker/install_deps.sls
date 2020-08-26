# TODO test glusterfs-docker

# required for docker-formula
yum_versionlock_installed:
  pkg.installed:
    - names:
      - yum-plugin-versionlock
      # salt warns about that package when docker is being installed,
      # it's required for some non trivial rpm versions comparison
      - rpmdevtools

# required for internal docker_* states
# TODO might be outdated in system repositories
#      but looks like Salt is ok with that
python_docker_installed:
  pkg.installed:
    - name: python36-docker
