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
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/files
mkdir -p %{buildroot}/opt/seagate/eos/eos-prvsnr

# Copy files
#cp -R cli %{buildroot}/opt/seagate/eos-prvsnr
cp -R pillar %{buildroot}/opt/seagate/eos-prvsnr
cp -R srv %{buildroot}/opt/seagate/eos-prvsnr
cp -R api %{buildroot}/opt/seagate/eos-prvsnr
cp -R files/syslogconfig %{buildroot}/opt/seagate/eos-prvsnr/files
cp -R files/conf %{buildroot}/opt/seagate/eos/eos-prvsnr


%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/eos-prvsnr/%{name}.yaml
#/opt/seagate/eos-prvsnr/cli
/opt/seagate/eos-prvsnr/pillar
/opt/seagate/eos-prvsnr/srv
/opt/seagate/eos-prvsnr/api
/opt/seagate/eos-prvsnr/files/syslogconfig
/opt/seagate/eos/eos-prvsnr/conf


# TODO test
%post
# adding prvsnrusers group
echo "Creating group 'prvsnrusers'..."
groupadd -f prvsnrusers
# set access rights for api users
#    user file root
mkdir -p /opt/seagate/eos-prvsnr/srv_user
chown -R :prvsnrusers /opt/seagate/eos-prvsnr/srv_user
chmod -R g+rws /opt/seagate/eos-prvsnr/srv_user
setfacl -Rdm g:prvsnrusers:rwx /opt/seagate/eos-prvsnr/srv_user
#    user pillar
mkdir -p /opt/seagate/eos-prvsnr/pillar/user
chown -R :prvsnrusers /opt/seagate/eos-prvsnr/pillar/user
chmod -R g+rws /opt/seagate/eos-prvsnr/pillar/user
setfacl -Rdm g:prvsnrusers:rwx /opt/seagate/eos-prvsnr/pillar/user

# install api globally using pip
pip3 install -U /opt/seagate/eos-prvsnr/api/python

%preun
# uninstall api globally using pip
pip3 uninstall -y eos-prvsnr
