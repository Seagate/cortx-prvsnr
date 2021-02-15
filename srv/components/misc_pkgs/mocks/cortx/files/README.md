# Quick Guide For Mock environment deployment

1. Install `rpm-build` and `rpmdevtools` rpm packages
```
sudo yum install rpm-build rpmdevtools
```

2. Move to `srv/components/misc_pkgs/mocks/cortx/files/scripts/` directory

2. Build mock RPMs for CORTX components:
```
./buildrpm.sh
```

3. Create mock repository
```
sudo ./configure_repo.sh /home/<Your UGID>
```

4. Apply mock environment configuration
```
sudo salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx.install
```