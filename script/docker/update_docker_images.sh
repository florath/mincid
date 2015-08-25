#!/bin/bash
#
# This script updates the docker images
#
# ToDo: Is special http proxy handling needed?

set -e

# Switch of any further deployment of jobs
scontrol update PartitionName=mincid State=DOWN

# Check / wait if all current jobs are finished

set +e
while true;
do
    # Check if there are (still) some jobs
    squeue -h -o "%.2t" | grep "R" >/dev/null 2>&1
    GRVAL=$?
    if test ${GRVAL} -ne 0;
    then
	break
    fi
    sleep 5
done
set -e

# Housekeeping
rm -fr /var/tmp/docker-mkimage*
##docker images -q | xargs --no-run-if-empty docker rmi -f

# Rinse is needed for RPM bases systems
# apt-get install rinse yum
# Centos 7
##/usr/share/docker.io/contrib/mkimage.sh -t centos:7 rinse --distribution centos-7
# This is needed to get the ubuntu signing key correct
# apt-get install ubuntu-archive-keyring
# Ubuntu 15.10 -> wily
/usr/share/docker.io/contrib/mkimage.sh -t ubuntu:wily debootstrap --include=ubuntu-minimal --components=main,universe wily
# Debian 8 -> jessie
/usr/share/docker.io/contrib/mkimage.sh -t debian:jessie debootstrap --variant=minbase jessie
# Debian 9 -> stretch
/usr/share/docker.io/contrib/mkimage.sh -t debian:stretch debootstrap --variant=minbase stretch

IIDS=$(docker images -q)

for iid in ${IIDS};
do
    docker save ${iid} >/mincid/build/system/docker/${iid}.tar
done

# Deploy all images on all nodes
NODELIST=$(sinfo -h -o "%n" -p mincid)

for node in ${NODELIST};
do
    # Remove all old images from this node
    docker images -q | xargs --no-run-if-empty docker rmi -f
    for tf in /mincid/build/system/docker/*.tar;
    do
	srun -w ${node} -p mincidctl docker load -i ${tf}
    done
done

# Switch on job handling
scontrol update PartitionName=mincid State=UP
