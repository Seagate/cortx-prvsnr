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
Requires: python36-pip
Requires: salt-master = 2019.2.0
Requires: salt-minion = 2019.2.0
#Requires: salt-ssh
#Requires: salt-syndic


%description
EOS Provisioning to deploy EOS Object storage software.


%prep
%setup -n %{name}-%{version}-%{_ees_prvsnr_git_ver}
rm -rf %{buildroot}


%build
# Turn off the brp-python-bytecompile automagic
%global _python_bytecompile_extra 0
%global __python %{__python3}



%install
# Create directories
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/{pillar,srv,files,api}

mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/files/etc/salt

# Copy files
cp -R files/etc/salt/* %{buildroot}/opt/seagate/eos-prvsnr/files/etc/salt/
cp -R pillar %{buildroot}/opt/seagate/eos-prvsnr/
cp -R srv %{buildroot}/opt/seagate/eos-prvsnr/
cp -R api %{buildroot}/opt/seagate/eos-prvsnr/


%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/eos-prvsnr/%{name}.yaml

/opt/seagate/eos-prvsnr/files/etc/salt
/opt/seagate/eos-prvsnr/pillar
/opt/seagate/eos-prvsnr/srv
/opt/seagate/eos-prvsnr/api


# TODO test
%post
mv -f /etc/salt/master /etc/salt/master.org
mv -f /etc/salt/minion /etc/salt/minion.org
cp -p /opt/seagate/eos-prvsnr/files/etc/salt/master /etc/salt/master
cp -p /opt/seagate/eos-prvsnr/files/etc/salt/minion /etc/salt/minion
# adding prvsnrusers group
groupadd prvsnrusers
# install api globally using pip
pip3 install /opt/seagate/eos-prvsnr/api/python

%preun
# uninstall api globally using pip
pip3 uninstall -y eos-prvsnr
# removing prvsnrusers group
groupdel prvsnrusers


# TODO test
%postun
mv -f /etc/salt/master.org /etc/salt/master
mv -f /etc/salt/minion.org /etc/salt/minion
