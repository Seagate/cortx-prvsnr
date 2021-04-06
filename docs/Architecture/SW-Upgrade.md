# SW Upgrade

Table of contents:

- [Setup SW upgrade repository](#setup-sw-upgrade-repository)
- [Apply SW upgrade](#apply-sw-upgrade)
- [SW upgrade single ISO bundle structure](#sw-upgrade-single-iso-bundle-structure)
- [Delete SW upgrade repository](#delete-sw-upgrade-repository)


## Setup SW upgrade repository

The common structure of the `set_swupgrade_repo` command:
```bash
provisioner set_swupgrade_repo </path/to/single/iso/bundle> --hash="<hash_type>:<hash> <filename>"  --hash-type="<hash_type>" \ 
--username=<provisioner_user> --password=<provisioner_user_password>`
```

where

`</path/to/single/iso/bundle>`: **Mandatory**. Path to the single SW upgrade ISO bundle file

`--hash="<hash_type>:<hash> <filename>"`: **Optional**. Setups hash value of single SW upgrade bundle ISO for verification.
Can be either string with hash data or path to the file with that data.
Supported formats of checksum string

1. <hash_type>:<check_sum> <file_name>
2. <hash_type>:<check_sum>
3. <check_sum> <file_name>
4. <check_sum>

where

- `<hash_type>`: one of the values from `config.HashType` enumeration. Supported values: `md5`, `sha256`, `sha512`.
- `<check_sum>`: hexadecimal representation of hash checksum
- `<file_name>`: a file name to which <hash_type> and <hash_sum> belongs to

 `--hash-type="<hash_type>"` **Optional**. Type of hash value. Supported values: `md5`, `sha256`, `sha512`. See `config.HashType` for all possible values. 

`--username=<provisioner_user>`: **Optional**. Provisioner user which has necessary permissions

`--password=<provisioner_user_password>`: **Optional**. Password of the provisioner user

Examples:
```bash
provisioner set_swupgrade_repo /opt/iso/single_cortx.iso --hash="fefa1db67588d2783b83f07f4f5beb5c"  --hash-type="md5" --username=123456 --password=123456
provisioner set_swupgrade_repo /opt/iso/single_cortx.iso --hash="sha256:ff01da01d4304729bfbad3aeca53b705c1d1d2132e94e4303c1ea210288de12b"
provisioner set_swupgrade_repo /opt/iso/single_cortx.iso --hash="md5:fefa1db67588d2783b83f07f4f5beb5c /opt/iso/single_cortx.iso"
```

## SW upgrade single ISO bundle structure

Expected minimum structure of single SW upgrade ISO bundle:
```
sw_upgrade_bundle.iso
    - 3rd_party/
        - THIRD_PARTY_RELEASE.INFO
    - cortx_iso/
        - RELEASE.INFO
    - python_deps/
    - os/
```

The following basic and minimum necessary structure of `RELEASE.INFO`

```yaml
RELEASE.INFO:
    NAME:
    RELEASE: (can be absent)
    VERSION:
    BUILD:
    OS:
    COMPONENTS:
```

All fields above except `RELEASE` are mandatory fields for the `RELEASE.INFO` file


## Apply SW upgrade

To initiate SW upgrade procedure run the command

```bash
provisioner sw_upgrade --targets=<hosts> --username=<provisioner_user> --password=<provisioner_user_password>
```

where

`--targets=<hosts>`: **Optional**. Hosts for SW upgrade

`--username=<provisioner_user>`: **Optional**. Provisioner user which has necessary permissions

`--password=<provisioner_user_password>`: **Optional**. Password of the provisioner user

## Delete SW upgrade repository

To remove installed SW upgrade repository run the command:
```bash
provisioner remove_swupgrade_repo <release> --username=<provisioner_user> --password=<provisioner_user_password>
```

where

`<release>`: **Mandatory**. Release version of the SW upgrade repository

`--username=<provisioner_user>`: **Optional**. Provisioner user which has necessary permissions

`--password=<provisioner_user_password>`: **Optional**. Password of the provisioner user

**NOTE:**

To see the list of SW upgrade repositories:
```bash
yum repolist
```
