Name:           cortx-s3server
Version:        2.0.0
Release:        0
Summary:        Cortx S3Server Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-s3server-2.0.0.tar.gz

%description
Cortx S3Server Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-s3server
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-s3server

%files
/opt/seagate/cortx/mocks/cortx-s3server
/opt/seagate/cortx/mocks/cortx-s3server/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial Cortx S3Server mock rpm release