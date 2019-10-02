Name:       eos-prvsnr-cli
Version:    %{_ees_prvsnr_version}
Release:    %{_build_number}_%{_ees_prvsnr_git_ver}_%{?dist:el7}
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

%clean
rm -rf %{buildroot}

%files
# %config(noreplace) /opt/seagate/eos-prvsnr/cli/%{name}.yaml

/opt/seagate/eos-prvsnr/cli

%post
# TBD
