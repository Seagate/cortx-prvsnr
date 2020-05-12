Name:       eos-prvsnr-cli
Version:    %{_ees_prvsnr_version}
Release:    %{_build_number}_%{_ees_prvsnr_git_ver}_%{?dist:el7}
Summary:    EOS Provisioner Command line interface.

Group:      Tools
License:    Seagate
URL:        http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr
Source:     %{name}-%{version}-%{_ees_prvsnr_git_ver}.tar.gz

BuildRequires: python36-devel

Requires: PyYAML
Requires: python36

%description
EOS Provisioner Command line interface. Provides utilities to deploy EOS Object storage.


%prep
%setup -n %{name}-%{version}-%{_ees_prvsnr_git_ver}


%build
# Turn off the brp-python-bytecompile automagic
%global _python_bytecompile_extra 0
%global __python %{__python3}


%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/{cli,files/etc}

cp -pr cli/src %{buildroot}/opt/seagate/eos-prvsnr/cli
cp -pr files/.ssh %{buildroot}/opt/seagate/eos-prvsnr/files
cp -pr files/etc/yum.repos.d %{buildroot}/opt/seagate/eos-prvsnr/files/etc


%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/eos-prvsnr/cli/%{name}.yaml
/opt/seagate/eos-prvsnr/cli
/opt/seagate/eos-prvsnr/files


%post
# TODO test
# TODO IMPROVE current workaround is to prevent conflicts
#              with provisioner main rpm instllation
cp -fpr /opt/seagate/eos-prvsnr/cli/src/* /opt/seagate/eos-prvsnr/cli
chmod -r 755 /opt/seagate/eos-prvsnr/cli

# TODO test
mkdir -p /root/.ssh
cp -pr /opt/seagate/eos-prvsnr/files/.ssh/* /root/.ssh/
chmod 700 /root/.ssh/
chmod 600 /root/.ssh/*

%postun
#TDB
