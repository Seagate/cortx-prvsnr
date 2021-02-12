Name:           cortx-csm_web
Version:        2.0.0
Release:        0
Summary:        Cortx CSM Web Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-csm_web-2.0.0.tar.gz

%description
Cortx CSM Web Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-csm_web
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-csm_web

%files
/opt/seagate/cortx/mocks/cortx-csm_web
/opt/seagate/cortx/mocks/cortx-csm_web/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial cortx csm web mock rpm release