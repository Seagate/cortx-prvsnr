Name:       cortx-node-cli
Version:    %{_cortx_prvsnr_version}
Release:    %{_build_number}.%{_cortx_prvsnr_git_ver}.%{?dist:el7}
Summary:    NodeCLI rpm.

Group:      Tools
License:    Seagate
URL:        https://github.com/Seagate/cortx-prvsnr
Source:     %{name}-%{version}-%{_cortx_prvsnr_git_ver}.tar.gz

BuildRequires: python36-devel

Requires: python36
Requires: python36-cortx-prvsnr
Requires: cortx-prvsnr
Requires: python36-cortx-setup


%description
NodeCLI rpm to deploy CORTX at Feild.


%prep
%setup -n %{name}-%{version}-%{_cortx_prvsnr_git_ver}
rm -rf %{buildroot}


%build
# Turn off the brp-python-bytecompile automagic
%global _python_bytecompile_extra 0
%global __python %{__python3}
# helps with newer builders (e.g. on centos 8.2)
%global debug_package %{nil}



%install
# Create directories
#mkdir -p %{buildroot}/opt/seagate/cortx/provisioner
mkdir -p %{buildroot}/opt/seagate/cortx/provisioner/{files,conf}

# Copy files
cp -R node_cli %{buildroot}/opt/seagate/cortx/provisioner/node_cli/

%post
# Set Permissions
ln -sf /opt/seagate/cortx/provisioner/node_cli/nodecli.py /usr/bin/node_cli

%clean
rm -rf %{buildroot}


%files
# %config(noreplace) /opt/seagate/cortx/provisioner/%{name}.yaml
/opt/seagate/cortx/provisioner/node_cli
