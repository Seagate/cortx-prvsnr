Name:           %{__NAME__}
Version:        %{__VERSION__}
Release:        %{__BUILD__}
Summary:        %{name} Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        %{name}-%{version}.tar.gz

%description
%{name} Mock RPM For Testing

%prep
%setup -q
rm -rf %{buildroot}

%build

%install
install -m 0755 -d %{buildroot}/opt/seagate/cortx/mocks/%{name}
mkdir -p %{buildroot}/opt/seagate/cortx/%{__COMPONENT__}/conf/
install -m 0644 setup.yaml %{buildroot}/opt/seagate/cortx/%{__COMPONENT__}/conf/setup.yaml

%files
/opt/seagate/cortx/mocks/%{name}
/opt/seagate/cortx/%{__COMPONENT__}/conf/setup.yaml

%clean
rm -rf %{buildroot}


%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial cortx cli mock rpm release
