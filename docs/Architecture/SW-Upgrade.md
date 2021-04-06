# SW Upgrade

Table of contents:

- [High Level SW Upgrade logic](#high-level-sw-upgrade-logic)
- [Setup SW upgrade repository](#setup-sw-upgrade-repository)
- [Apply SW upgrade](#apply-sw-upgrade)
- [SW upgrade single ISO bundle structure](#sw-upgrade-single-iso-bundle-structure)
- [Delete SW upgrade repository](#delete-sw-upgrade-repository)
- [References](#references)


## High Level SW Upgrade logic

The high level logic of SW upgrade is:

    1. Validate candidate SW upgrade single ISO bundle:
        a. Mount ISO
        b. ISO catalog structure validation
        c. Validate content of `RELEASE.INFO` file for each separate bundle's repository
        d. Setup yum repositories
        e. Validate each separate yum repo
    2. SW upgrade repositories setup:
        a. Mount ISO
        b. Setup yum repositories
        c. Return the metadata information about installed SW upgrade repositories

## Setup SW upgrade repository

The common structure of the `set_swupgrade_repo` command:
```bash
provisioner set_swupgrade_repo </path/to/single/iso/bundle> --hash="<hash_type>:<hash> <filename>"  --hash-type="<hash_type>"
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

:warning: **NOTE**: The `md5` is the default hash type. So you can omit hash type in `--hash` and in `--hash-type` options.
Hash type in `--hash` option has the higher priority than `--hash-type`.
As mentioned in the `--hash` option description, you can specify a path to a file that contains hash data. The format of this file is
the same as for the hash string.

See [Passing crdedentials to CLI](#passing-crdedentials-to-cliapipythonreadmemdpassing-crdedentials-to-cli) how to pass
credential for command authorization.

Examples:
```bash
provisioner set_swupgrade_repo /opt/iso/single_cortx.iso --hash="fefa1db67588d2783b83f07f4f5beb5c"
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
provisioner sw_upgrade --targets=<hosts>
```

where

`--targets=<hosts>`: **Optional**. Hosts for SW upgrade

See [Passing crdedentials to CLI](#passing-crdedentials-to-cliapipythonreadmemdpassing-crdedentials-to-cli) how to pass
credential for command authorization.

## Delete SW upgrade repository

To remove installed SW upgrade repository run the command:
```bash
provisioner remove_swupgrade_repo <release>
```

where

`<release>`: **Mandatory**. Release version of the SW upgrade repository

See [Passing crdedentials to CLI](#passing-crdedentials-to-cliapipythonreadmemdpassing-crdedentials-to-cli) how to pass
credential for command authorization.

:warning: **NOTE**:

To see the list of SW upgrade repositories:
```bash
yum repolist
```


## References

#### [Passing crdedentials to CLI](../../api/python/README.md#passing-crdedentials-to-cli)
