# Before proceeding with Server setup refer to:

* [Vagrant Setup](VagrantSetup.md)
* [SaltStack Setup](SaltStackSetup.md)

# Preparing Config Files

S3Client provisioning formula refers to the required data in **_pillar/components/s3client.sls_**

```
s3client:
  s3server:
    fqdn: srvnode-1
    ip: 127.0.0.1        # Optional if FQDN is under DNS
  access_key: 2lB1wnQKSw2gehG68SzHwA
  secret_key: Z/xFyapiUnfUBGAXsK+DdJbrQEEyyTie5+uOylO0
  region: US
  output: text      # json/text/table
  s3endpoint: s3.seagate.com
```

**OR**

Run script to set the s3client config:

```
$ cd /opt/seagate/cortx/provisioner
$ python3 ./utils/configure-eos.py --show-s3client-file-format
$ python3 ./utils/configure-eos.py --s3client-file <yaml_file_generated_based_on_output_above>
```

## Set target release version to be installed

```
$ cat <prvsnr source>/pillar/components/release.sls
release:
    target_build: last_successful
```

**OR**

Run script to set the release tag:

`$ provisioner pillar_set release/target_build \"<URL_for_build_repo>\"`  


# Setup S3Client

Execute Salt formula to setup:

`$ salt-call state.apply components.s3clients`  

This implicitly installs:

* S3IAMCLI
* S3Cmd
* AWSCLI

To uninstall:

`$ salt-call --local state.apply components.s3clients.teardown`

## Independent Setup

### S3Cmd

To setup:

`$ salt-call --local state.apply components.s3client.s3cmd`

To teardown:

`$ salt-call --local state.apply components.s3client.s3cmd.teardown`


### AWSCli

To setup:

`$ salt-call --local state.apply components.s3client.awscli`

To teardown:

`$ salt-call --local state.apply components.s3client.awscli.teardown`


# Setup COSBench

To setup:

`$ salt-call --local state.apply components.performance_testing.cosbench`

To teardown:

`$ salt-call --local state.apply components.performance_testing.cosbench.teardown`
