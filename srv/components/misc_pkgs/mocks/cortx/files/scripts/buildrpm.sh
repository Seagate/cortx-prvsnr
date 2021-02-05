#!/bin/bash

VERSION="2.0.0"

WORKING_DIR=${PWD}/../
BUILD_DIR=$(realpath ~)

cd ${BUILD_DIR}

rm -rf ${BUILD_DIR}/rpmbuild

rpmdev-setuptree

cp -r ${WORKING_DIR}/specs/* "${BUILD_DIR}/rpmbuild/SPECS/"

cd "$BUILD_DIR/rpmbuild/"
ls SPECS/ | sed -E "s/(.*).spec/\1-${VERSION}/" | xargs -I{} mkdir -p ./SOURCES/{}
ls SOURCES/ | xargs -I{} touch SOURCES/{}/mock.txt

cd SOURCES/
ls ./ | xargs -I{} tar czf {}.tar.gz {}

cd ../
ls SPECS/ | xargs -I{} rpmbuild -ba SPECS/{}

cd ${WORKING_DIR}
