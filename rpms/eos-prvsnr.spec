# build number
%define build_num  %( test -n "$build_number" && echo "$build_number" || echo 1 )

Name:       eos-prvsnr
Version:    %{_ees_prvsnr_version}
Release:    %{build_num}_%{_ees_prvsnr_git_ver}_%{?dist:el7}
Summary:    EOS Provisioning.

Group:      Tools
License:    Seagate
URL:        http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr
Source:     %{name}-%{version}-%{_ees_prvsnr_git_ver}.tar.gz

BuildRequires: python36
BuildRequires: PyYAML

Requires: python36
Requires: salt-master
Requires: salt-minion
Requires: salt-ssh
Requires: salt-syndic
Requires: PyYAML

%description
EOS Provisioning to deploy EOS Object storage software.

%prep
%setup -n %{name}-%{version}-%{_ees_prvsnr_git_ver}

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/{files,pillar,srv,utils}
cp -R files %{buildroot}/opt/seagate/eos-prvsnr/
cp -R pillar %{buildroot}/opt/seagate/eos-prvsnr/
cp -R srv %{buildroot}/opt/seagate/eos-prvsnr/
cp -R utils %{buildroot}/opt/seagate/eos-prvsnr/
exit 0

%clean
rm -rf %{buildroot}

%files
# %config(noreplace) /opt/seagate/eos-prvsnr/%{name}.yaml

/opt/seagate/eos-prvsnr/files
/opt/seagate/eos-prvsnr/pillar
/opt/seagate/eos-prvsnr/srv
/opt/seagate/eos-prvsnr/utils

%post
# TBD
