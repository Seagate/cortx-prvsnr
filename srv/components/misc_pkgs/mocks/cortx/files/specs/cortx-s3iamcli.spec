Name:           cortx-s3iamcli
Version:        2.0.0
Release:        0
Summary:        Cortx S3iamcli Mock RPM

Group:          Testing environment
BuildArch:      noarch
License:        Seagate
URL:            https://github.com/Seagate/cortx-prvsnr
Source0:        cortx-s3iamcli-2.0.0.tar.gz

%description
Cortx s3iamcli Mock RPM For Testing

%prep
%setup -q
%build
%install
install -m 0755 -d $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-s3iamcli
install -m 0644 mock.txt $RPM_BUILD_ROOT/opt/seagate/cortx/mocks/cortx-s3iamcli

%files
/opt/seagate/cortx/mocks/cortx-s3iamcli
/opt/seagate/cortx/mocks/cortx-s3iamcli/mock.txt

%changelog
* Tue Feb 02 2021 Dmitry Didenko  2.0.0
  - Initial Cortx S3iamcli mock rpm release