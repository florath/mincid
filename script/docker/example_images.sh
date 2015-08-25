# This is needed to get the ubuntu signing key correct
# apt-get install ubuntu-archive-keyring
# Ubuntu 15.10 -> wily
/usr/share/docker.io/contrib/mkimage.sh -t ubuntu:wily debootstrap --include=ubuntu-minimal --components=main,universe wily
# Debian 8 -> jessie
/usr/share/docker.io/contrib/mkimage.sh -t debian:jessie debootstrap --variant=minbase jessie
# Debian 9 -> stretch
/usr/share/docker.io/contrib/mkimage.sh -t debian:stretch debootstrap --variant=minbase stretch
# Rinse is needed for RPM bases systems
# apt-get install rinse yum
# Centos 7
/usr/share/docker.io/contrib/mkimage.sh -t centos:7 rinse --distribution centos-7
