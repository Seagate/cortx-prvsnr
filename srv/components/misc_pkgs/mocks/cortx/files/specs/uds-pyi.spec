Name:           uds-pyi
Version:        2.0.0
Release:        0
Summary:        Cortx UDS-Pyi Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        uds-pyi-2.0.0.tar.gz

%description
Cortx UDS-Pyi Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/uds-pyi
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/uds-pyi

%files
/opt/seagate/cortx/mocks/uds-pyi
/opt/seagate/cortx/mocks/uds-pyi/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial uds pyi mock rpm release