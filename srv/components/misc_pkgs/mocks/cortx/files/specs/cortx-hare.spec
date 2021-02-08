Name:           cortx-hare
Version:        2.0.0
Release:        0
Summary:        Cortx Hare Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-hare-2.0.0.tar.gz

%description
Cortx Hare Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-hare
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-hare

%files
/opt/seagate/cortx/mocks/cortx-hare
/opt/seagate/cortx/mocks/cortx-hare/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial Cortx Hare mock rpm release