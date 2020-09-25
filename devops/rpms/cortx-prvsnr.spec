Name:       cortx-prvsnr
Version:    %{_cortx_prvsnr_version}
Release:    %{_build_number}_%{_cortx_prvsnr_git_ver}_%{?dist:el7}
Summary:    CORTX Provisioning.

Group:      Tools
License:    Seagate
URL:        https://github.com/Seagate/cortx-prvsnr
Source:     %{name}-%{version}-%{_cortx_prvsnr_git_ver}.tar.gz

BuildRequires: python36-devel

Requires: python36
Requires: python36-PyYAML
Requires: python36-pip
Requires: rsync
#Requires: salt-master = 2019.2.0
#Requires: salt-minion = 2019.2.0
#Requires: salt-ssh
#Requires: salt-syndic


%description
CORTX Provisioning to deploy CORTX Object storage software.


%prep
%setup -n %{name}-%{version}-%{_cortx_prvsnr_git_ver}
rm -rf %{buildroot}


%build
# Turn off the brp-python-bytecompile automagic
%global _python_bytecompile_extra 0
%global __python %{__python3}



%install
# Create directories
#mkdir -p %{buildroot}/opt/seagate/cortx/provisioner
mkdir -p %{buildroot}/opt/seagate/cortx/provisioner/conf

# Copy files
cp -R api %{buildroot}/opt/seagate/cortx/provisioner
cp -R cli %{buildroot}/opt/seagate/cortx/provisioner
cp -R pillar %{buildroot}/opt/seagate/cortx/provisioner
cp -R srv %{buildroot}/opt/seagate/cortx/provisioner
cp -R srv/components/provisioner/files/setup.yaml %{buildroot}/opt/seagate/cortx/provisioner/conf/


%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/cortx/provisioner/%{name}.yaml
/opt/seagate/cortx/provisioner/conf
/opt/seagate/cortx/provisioner/api
/opt/seagate/cortx/provisioner/cli
/opt/seagate/cortx/provisioner/pillar
/opt/seagate/cortx/provisioner/srv
