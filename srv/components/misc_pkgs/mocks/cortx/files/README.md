# Quick Guide For Mock environment deployment

1. Install `rpm-build` and `rpmdevtools` rpm packages
```bash
sudo yum install rpm-build rpmdevtools
```

2. Move to `srv/components/misc_pkgs/mocks/cortx/files/scripts/` directory

3. Build mock RPMs for CORTX components:
```bash
./buildrpm.sh
```

4. Create mock repository
```bash
sudo ./configure_repo.sh /home/<Your UGID>
```

5. Apply mock environment configuration
```bash
sudo salt "srvnode-1" state.apply components.misc_pkgs.mocks.cortx.install
```
