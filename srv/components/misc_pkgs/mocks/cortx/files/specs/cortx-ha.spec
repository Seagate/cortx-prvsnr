Name:           cortx-ha
Version:        2.0.0
Release:        0
Summary:        Cortx HA Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-ha-2.0.0.tar.gz

%description
Cortx HA Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-ha
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-ha

%files
/opt/seagate/cortx/mocks/cortx-ha
/opt/seagate/cortx/mocks/cortx-ha/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial Cortx-HA mock rpm release