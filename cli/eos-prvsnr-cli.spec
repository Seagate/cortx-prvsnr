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
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/cli/utils
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/files/etc/modprobe.d
#mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/files/etc/sysconfig/network-scripts
mkdir -p %{buildroot}/opt/seagate/eos-prvsnr/files/etc/yum.repos.d
mkdir -p /root/.ssh
cp -pr cli/* %{buildroot}/opt/seagate/eos-prvsnr/cli/
cp -pr files/etc/modprobe.d/bonding.conf %{buildroot}/opt/seagate/eos-prvsnr/files/etc/modprobe.d/
#cp -p files/etc/sysconfig/network-scripts/ifcfg-* %{buildroot}/opt/seagate/eos-prvsnr/files/etc/sysconfig/network-scripts/
cp -pr files/etc/yum.repos.d/* %{buildroot}/opt/seagate/eos-prvsnr/files/etc/yum.repos.d/
cp -pr files/.ssh/* /root/.ssh/
chmod 755 /root/.ssh/
chmod 600 /root/.ssh/id_rsa


%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/eos-prvsnr/cli/%{name}.yaml
/opt/seagate/eos-prvsnr/cli
/opt/seagate/eos-prvsnr/files/etc
/root/.ssh


%post
# TBD
