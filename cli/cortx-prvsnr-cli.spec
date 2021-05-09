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
    
/bin/rm -rf %{buildroot}

/bin/mkdir -p %{buildroot}/opt/seagate/cortx/provisioner/{cli,files/etc,files/.ssh}

/bin/cp -pr cli/src %{buildroot}/opt/seagate/cortx/provisioner/cli
/bin/cp -pr files/etc/yum.repos.d %{buildroot}/opt/seagate/cortx/provisioner/files/etc

if [[ -e %{buildroot}/opt/seagate/cortx/provisioner/cortx/srv/system/files/.ssh/ ]]; then
  /bin/rm -rf %{buildroot}/opt/seagate/cortx/provisioner/cortx/srv/system/files/.ssh
fi

%clean
/bin/rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/cortx/provisioner/cli/%{name}.yaml
/opt/seagate/cortx/provisioner/cli
/opt/seagate/cortx/provisioner/files


%post
# TODO test
# TODO IMPROVE current workaround is to prevent conflicts
#              with provisioner main rpm instllation
/bin/cat <<EOL > ssh_config
Host srvnode-1 srvnode-1.localdomain
    HostName srvnode-1.localdomain
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile /root/.ssh/id_rsa_prvsnr
    IdentitiesOnly yes
    LogLevel ERROR
    BatchMode yes

Host srvnode-2 srvnode-2.localdomain
    HostName srvnode-2.localdomain
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile /root/.ssh/id_rsa_prvsnr
    IdentitiesOnly yes
    LogLevel ERROR
    BatchMode yes
EOL

#/bin/ssh-keygen -o -q -t rsa -b 4096 -a 100 -N '' -f id_rsa_prvsnr
#/bin/mv id_rsa_prvsnr* /opt/seagate/cortx/provisioner/files/.ssh
#/bin/mv ssh_config /opt/seagate/cortx/provisioner/files/.ssh
#/bin/cp -fpr /opt/seagate/cortx/provisioner/cli/src/* /opt/seagate/cortx/provisioner/cli
#/bin/chmod -R 750 /opt/seagate/cortx/provisioner/cli

# TODO test
/bin/mkdir -p /root/.ssh

## Ensure update replaces the keys
#if [[ -e /root/.ssh/id_rsa_prvsnr ]]; then
#  /bin/rm -f /root/.ssh/id_rsa_prvsnr || true
#  /bin/rm -f /root/.ssh/id_rsa_prvsnr.pub || true
#fi


if [[ ! -e /root/.ssh/config ]]; then

  /bin/ssh-keygen -o -q -t rsa -b 4096 -a 100 -N '' -f id_rsa_prvsnr
  /bin/mv id_rsa_prvsnr* /opt/seagate/cortx/provisioner/files/.ssh
  /bin/mv ssh_config /opt/seagate/cortx/provisioner/files/.ssh
  /bin/cp -fpr /opt/seagate/cortx/provisioner/cli/src/* /opt/seagate/cortx/provisioner/cli
  /bin/chmod -R 750 /opt/seagate/cortx/provisioner/cli

  /bin/cp -pr /opt/seagate/cortx/provisioner/files/.ssh/id_rsa_prvsnr /root/.ssh/
  /bin/cp -pr /opt/seagate/cortx/provisioner/files/.ssh/id_rsa_prvsnr.pub /root/.ssh/
  /bin/cat /root/.ssh/id_rsa_prvsnr.pub >>/root/.ssh/authorized_keys
  /bin/cp -pr /opt/seagate/cortx/provisioner/files/.ssh/ssh_config /root/.ssh/config
fi

/bin/chmod 700 /root/.ssh/
/bin/chmod 644 /root/.ssh/*
/bin/chmod 600 /root/.ssh/id_rsa_prvsnr
/bin/chmod 600 /root/.ssh/config

%postun
# Remove only during uninstall
if [[ $1 == 0  ]]; then
  # Ensure update replaces the keys
  /bin/echo "RPM is getting uninstalled, hence remove .ssh entries"
  /bin/rm -f /root/.ssh/id_rsa_prvsnr || true
  /bin/rm -f /root/.ssh/id_rsa_prvsnr.pub || true
  /bin/rm -f /root/.ssh/authorized_keys || true
  /bin/rm -f /root/.ssh/config || true 
fi
