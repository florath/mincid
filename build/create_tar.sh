#!/bin/bash
#
# Create release tarball
#

PRJNAME=mincid

# Build it outside the source tree
PKGBUILDDIR="../pbuild"

set -e

if test $# -ne 1;
then
    echo "Usage: create_tar.sh <ReleaseNum>"
    exit 1
fi

RELNUM=$1

rm -fr ${PKGBUILDDIR}
mkdir -p ${PKGBUILDDIR}

git tag ${RELNUM}
git archive --format=tar --prefix=${PRJNAME}-${RELNUM}/ ${RELNUM} | tar -C ${PKGBUILDDIR} -xf -

cd ${PKGBUILDDIR}/${PRJNAME}-${RELNUM}
# bash ./build/init_autotools.sh

cd ..
tar -cf - ${PRJNAME}-${RELNUM} | xz -c -9 >${PRJNAME}-${RELNUM}.tar.xz

