Name:       eos-prvsnr
Version:    %{_ees_prvsnr_version}
Release:    %{_build_number}_%{_ees_prvsnr_git_ver}_%{?dist:el7}
Summary:    EOS Provisioning.

Group:      Tools
License:    Seagate
URL:        http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr
Source:     %{name}-%{version}-%{_ees_prvsnr_git_ver}.tar.gz

BuildRequires: python36-devel

Requires: python36
Requires: python36-PyYAML
Requires: salt-master
Requires: salt-minion
#Requires: salt-ssh
#Requires: salt-syndic


%description
EOS Provisioning to deploy EOS Object storage software.


%prep
%setup -n %{name}-%{version}-%{_ees_prvsnr_git_ver}
rm -rf %{buildroot}


%install
# Create directories
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/{pillar,srv,files}
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/files/etc/salt
mkdir -p %{buildroot}/etc/yum.repos.d

# Copy files
cp -R files/etc/yum.repos.d/saltstack.repo %{buildroot}/etc/yum.repos.d/saltstack.repo
cp -R files/etc/salt/master %{buildroot}/opt/seagate/eos-prvsnr/files/etc/salt/master
cp -R files/etc/salt/minion %{buildroot}/opt/seagate/eos-prvsnr/files/etc/salt/minion
cp -R pillar %{buildroot}/opt/seagate/eos-prvsnr/
cp -R srv %{buildroot}/opt/seagate/eos-prvsnr/


%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/eos-prvsnr/%{name}.yaml

/etc/yum.repos.d/saltstack.repo
/opt/seagate/eos-prvsnr/files/etc/salt/master
/opt/seagate/eos-prvsnr/files/etc/salt/minion
/opt/seagate/eos-prvsnr/pillar
/opt/seagate/eos-prvsnr/srv


%post
cp -p /opt/seagate/eos-prvsnr/files/etc/salt/master /etc/salt/master
cp -p /opt/seagate/eos-prvsnr/files/etc/salt/minion /etc/salt/minion
