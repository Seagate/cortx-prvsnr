Name:           cortx-motr
Version:        2.0.0
Release:        0
Summary:        Cortx Motr Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-motr-2.0.0.tar.gz

%description
Cortx Motr Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-motr
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-motr

%files
/opt/seagate/cortx/mocks/cortx-motr
/opt/seagate/cortx/mocks/cortx-motr/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial Cortx Motr mock rpm release