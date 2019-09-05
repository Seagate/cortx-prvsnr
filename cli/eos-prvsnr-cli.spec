# build number
%define build_num  %( test -n "$build_number" && echo "$build_number" || echo 1 )

Name:       eos-prvsnr-cli
Version:    %{_ees_prvsnr_version}
Release:    %{build_num}_%{_ees_prvsnr_git_ver}_%{?dist:el7}
Summary:    EOS Provisioner Command line interface.

Group:      Tools
License:    Seagate
URL:        http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr
Source:     %{name}-%{version}-%{_ees_prvsnr_git_ver}.tar.gz

BuildRequires: python36

Requires: python36
Requires: PyYAML

%description
EOS Provisioner Command line interface. Provides utilities to deploy EOS Object storage.

%prep
%setup -n %{name}-%{version}-%{_ees_prvsnr_git_ver}

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/cli
cp -p -R cli/src/* %{buildroot}/opt/seagate/eos-prvsnr/cli/
#mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/files
#cp -p -R files %{buildroot}/opt/seagate/eos-prvsnr/

%clean
rm -rf %{buildroot}

%files
# %config(noreplace) /opt/seagate/eos-prvsnr/cli/%{name}.yaml

#/opt/seagate/eos-prvsnr/files
/opt/seagate/eos-prvsnr/cli/setup-provisioner
/opt/seagate/eos-prvsnr/cli/configure-eos
/opt/seagate/eos-prvsnr/cli/deploy-eos
/opt/seagate/eos-prvsnr/cli/bootstrap-eos
/opt/seagate/eos-prvsnr/cli/start-eos
/opt/seagate/eos-prvsnr/cli/stop-eos
/opt/seagate/eos-prvsnr/cli/update-eos
/opt/seagate/eos-prvsnr/cli/destroy-eos

%post
# TBD
