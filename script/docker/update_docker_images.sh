#!/bin/bash
#
# This script updates the docker images
#
# ToDo: Is special http proxy handling needed?

if test $# -le 1;
then
    echo "Usage: update_docker_images BASE_URL DOCKER_IMAGE1 DOCKER_IMAGE2 ..."
    exit 1;
fi

IMAGE_BASE_URL=$1
shift
DOCKER_IMAGES=$@

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
rm -fr /mincid/build/system/docker/*
docker images -q | xargs --no-run-if-empty docker rmi -f

# It is assumed, that the docker images are build (each night)
# on a dedicated server.  The images can be downloaded by wget.
(cd /mincid/build/system/docker
 for docker_image in ${DOCKER_IMAGES}; do
     wget ${IMAGE_BASE_URL}/${docker_image}
 done
)

# Deploy all images on all nodes
NODELIST=$(sinfo -h -o "%n" -p mincid)
# Create shell script to add all images
mkdir -p /mincid/build/system
NISH="/mincid/build/system/nish.sh"
rm -f ${NISH}
echo "#!/bin/bash" >>${NISH}
echo "docker images -q | xargs --no-run-if-empty docker rmi -f" >>${NISH}
for tf in /mincid/build/system/docker/*.tar.xz;
do
    echo "docker load -i ${tf}" >>${NISH}
done
chmod a+x ${NISH}

for node in ${NODELIST};
do
    # Remove all old images from this node
    echo "Handling node [${node}]"
    srun -w ${node} -p mincidctl ${NISH}
done

# Switch on normal job handling
scontrol update PartitionName=mincid State=UP
