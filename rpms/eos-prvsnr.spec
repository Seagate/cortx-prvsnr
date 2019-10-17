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

# Copy files
cp -R files/etc/salt/* %{buildroot}/opt/seagate/eos-prvsnr/files/etc/salt/
cp -R pillar %{buildroot}/opt/seagate/eos-prvsnr/
cp -R srv %{buildroot}/opt/seagate/eos-prvsnr/


%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/eos-prvsnr/%{name}.yaml

/opt/seagate/eos-prvsnr/files/etc/salt
/opt/seagate/eos-prvsnr/pillar
/opt/seagate/eos-prvsnr/srv


# TODO test
%post
mv -f /etc/salt/master /etc/salt/master.org
mv -f /etc/salt/minion /etc/salt/minion.org
cp -p /opt/seagate/eos-prvsnr/files/etc/salt/master /etc/salt/master
cp -p /opt/seagate/eos-prvsnr/files/etc/salt/minion /etc/salt/minion

# TODO test
%postun
mv -f /etc/salt/master.org /etc/salt/master
mv -f /etc/salt/minion.org /etc/salt/minion
