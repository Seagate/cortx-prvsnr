#!/bin/bash

set -eux

pip3_package="$(repoquery --qf='%{name}' --pkgnarrow=all 'python3-pip' | head -n1)"

if [[ -z "$pip3_package" ]]; then
    pip3_package="$(repoquery --qf='%{name}' --pkgnarrow=all 'python36-pip')"
fi

if [[ -z "$pip3_package" ]]; then
    >&2 echo "Package for pip3 is not found"
    exit 1
fi

yum install -y "$pip3_package"
