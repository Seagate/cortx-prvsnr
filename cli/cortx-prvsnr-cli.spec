Name:       cortx-prvsnr-cli
Version:    %{_cortx_prvsnr_version}
Release:    %{_build_number}_%{_cortx_prvsnr_git_ver}_%{?dist:el7}
Summary:    CORTX Provisioner Command line interface.

Group:      Tools
License:    Seagate
URL:        https://github.com/Seagate/cortx-prvsnr
Source:     %{name}-%{version}-%{_cortx_prvsnr_git_ver}.tar.gz

BuildRequires: python36-devel

Requires: PyYAML
Requires: python36

%description
CORTX Provisioner Command line interface. Provides utilities to deploy CORTX Object storage.


%prep
%setup -n %{name}-%{version}-%{_cortx_prvsnr_git_ver}


%build
# Turn off the brp-python-bytecompile automagic
%global _python_bytecompile_extra 0
%global __python %{__python3}


%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/opt/seagate/cortx/provisioner/{cli,files/etc}

cp -pr cli/src %{buildroot}/opt/seagate/cortx/provisioner/cli
cp -pr files/etc/yum.repos.d %{buildroot}/opt/seagate/cortx/provisioner/files/etc

if [[ -e %{buildroot}/opt/seagate/cortx/provisioner/files/.ssh ]]; then
  rm -rf %{buildroot}/opt/seagate/cortx/provisioner/files/.ssh
fi

%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/cortx/provisioner/cli/%{name}.yaml
/opt/seagate/cortx/provisioner/cli
/opt/seagate/cortx/provisioner/files


%post
# TODO test
# TODO IMPROVE current workaround is to prevent conflicts
#              with provisioner main rpm instllation
cp -fpr /opt/seagate/cortx/provisioner/cli/src/* /opt/seagate/cortx/provisioner/cli
chmod -R 750 /opt/seagate/cortx/provisioner/cli

# TODO test
mkdir -p /root/.ssh

# Ensure update replaces the keys
if [[ -e /root/.ssh/id_rsa_prvsnr ]]; then
  rm -f /root/.ssh/id_rsa_prvsnr || true
  rm -f /root/.ssh/id_rsa_prvsnr.pub || true
fi

cp -pr /opt/seagate/cortx/provisioner/files/.ssh/id_rsa_prvsnr /root/.ssh/
cp -pr /opt/seagate/cortx/provisioner/files/.ssh/id_rsa_prvsnr.pub /root/.ssh/
cat /root/.ssh/id_rsa_prvsnr.pub >>/root/.ssh/authorized_keys

if [[ ! -e /root/.ssh/config ]]; then
  cp -pr /opt/seagate/cortx/provisioner/files/.ssh/config /root/.ssh/
fi

chmod 700 /root/.ssh/
chmod 600 /root/.ssh/*

%postun
# Remove only during uninstall
if [[ $1 == 0  ]]; then
  # Ensure update replaces the keys
  echo "RPM is getting uninstalled, hence remove .ssh entries"
  rm -f /root/.ssh/id_rsa_prvsnr || true
  rm -f /root/.ssh/id_rsa_prvsnr.pub || true
  rm -f /root/.ssh/authorized_keys || true
  rm -f /root/.ssh/config || true
fi
