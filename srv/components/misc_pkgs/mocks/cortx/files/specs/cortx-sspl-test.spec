Name:           cortx-sspl-test
Version:        2.0.0
Release:        0
Summary:        Cortx SSPL Test Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-sspl-test-2.0.0.tar.gz

%description
Cortx SSPL Test Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-sspl-test
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-sspl-test

%files
/opt/seagate/cortx/mocks/cortx-sspl-test
/opt/seagate/cortx/mocks/cortx-sspl-test/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial cortx sspl test mock rpm release