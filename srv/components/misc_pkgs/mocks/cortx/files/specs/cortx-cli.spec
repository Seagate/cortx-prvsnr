Name:           cortx-cli
Version:        2.0.0
Release:        0
Summary:        Cortx CLI Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-cli-2.0.0.tar.gz

%description
Cortx CLI Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-cli
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-cli

%files
/opt/seagate/cortx/mocks/cortx-cli
/opt/seagate/cortx/mocks/cortx-cli/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial cortx cli mock rpm release