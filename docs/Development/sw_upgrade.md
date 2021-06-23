# Software Upgrade Development Design

## Table of Contents

*   [Software Upgrade Commands](#software-upgrade-commands)



## Software Upgrade Commands

### set_swupgrade_repo

This command is used for software upgrade repositories setup and configuration. The command takes one mandatory parameter - path to the SW upgrade ISO bundle.

The common command structure
```shell
provisioner set_swupgrade_repo <path-to-upgrade-ISO> \
            --sig-file <path-to-signature-file> --gpg-pub-key <path-to-GPG-public-key> \
            --hash="<hash_type>:<hash> <filename>" --hash-type="<hash_type>"
```

`<path-to-upgrade-ISO>`  - Path to the ISO with SW upgrade repositories. It is the mandatory parameter.

`--sig-file <path-to-signature-file>` - Path to the file that contains signature of the SW upgrade ISO. It is the optional parameter. 
If parameter is specified, the authenticity check for SW upgrade ISO would be done.

`--gpg-pub-key <path-to-GPG-public-key>` - It is the optional parameter. It specifies the custom path to the GPG public key. 
ISO authenticity validation will be performed with provided GPG public key instead of default GPG keyring.

`--hash="<hash_type>:<hash> <filename>"` -  It is the optional parameter. Setups hash value of single SW upgrade bundle ISO for verification. 
                                            Can be either string with hash data or path to the file with that data. Supported formats of checksum string:

```text
<hash_type>:<check_sum> <file_name>
<hash_type>:<check_sum>
<check_sum> <file_name>
<check_sum>
```

where

`<hash_type>` - one of the values from config.HashType enumeration. Supported values: md5, sha256, sha512.

`<check_sum>` - hexadecimal representation of hash checksum

`<file_name>` - a file name to which <hash_type> and <hash_sum> belongs to

`--hash-type="<hash_type>"` - It is the optional parameter. Type of hash value. Supported values: `md5`, `sha256`, `sha512`. See config.HashType for all possible values.

:warning: NOTE: The md5 is the default hash type. So you can omit hash type in `--hash` and in `--hash-type` options. 
Hash type in `--hash` option has the higher priority than `--hash-type`. As mentioned in the `--hash` option description, 
you can specify a path to a file that contains hash data. The format of this file is the same as for the hash string.



### get_swupgrade_info

The command is useful to get CORTX SW upgrade repository metadata (the content of RELEASE.INFO file).

Without any parameters returns metadata of the last applied SW upgrade ISO bundle.

The command takes 2 optional parameters:

`--iso-path` - Path to the custom SW upgrade ISO bundle. If specified, the command returns metadata of provided ISO bundle.

`--release` - Custom SW upgrade release version. It may be useful in case of multiple SW upgrade configured repositories 
              and there is a need to get metadata of a specific upgrade version.

### get_iso_version

The command returns version of an active SW upgrade ISO (version of the last applied SW upgrade ISO). This command doesn't’t take any parameters.


### check_iso_authenticity

It is the command to check standalone SW upgrade ISO authenticity.

Parameters are the following:

`--iso-path` - Path to the custom SW upgrade ISO bundle for authenticity validation. It is the mandatory parameter. 
By default, the command performs validation against the default GPG keyring.

`--sig-file <path-to-signature-file>` - Path to the file that contains signature of the SW upgrade ISO. It is a mandatory parameter.

`--gpg-pub-key <path-to-GPG-public-key>` - It is optional parameter. It specifies the custom path to the GPG public key. 
ISO authenticity validation will be performed with provided GPG public key instead of the default GPG keyring.


### remove_swupgrade_repo

That command is useful to perform removing of already setup SW upgrade repository. This command takes only one positional argument - release version of SW upgrade
repository in the format like `2.0.0-277`:

```shell
provisioner remove_swupgrade_repo <release-version>
```

where `<release-version>` is release version of SW upgrade repository. It consists of two parts `<VERSION>` and `<BUILD>`: `<VERSION>-<BUILD>`,
where values `<VERSION>` and `<BUILD>` correspond to the `VERSION` and `BUILD` fields of `RELEASE.INFO` file.

