Name:           cortx-csm_agent
Version:        2.0.0
Release:        0
Summary:        Cortx CSM Agent Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-csm_agent-2.0.0.tar.gz

%description
Cortx CSM Agent Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-csm_agent
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-csm_agent

%files
/opt/seagate/cortx/mocks/cortx-csm_agent
/opt/seagate/cortx/mocks/cortx-csm_agent/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial cortx csm agent mock rpm release