# Install mincid
The installation process consists of some steps:
* Setting up the central / main mincid server
* Setting up some build nodes

## Needed Resources
The master node needs not that much 

## Create Golden Image VM
The base systems for all mincid VMs in this installation tutorial is
Debian Stretch.  You can use another system - but have to adapt the
installation at some points.

To simplify the installation of the VMs that are needed - in this
tutorial we will install one central node VM and three build nodes -
once a golden image of Debian Stretch is created that will be used for
all these systems.

A (detailed description)[InstallDetailsGoldenImage.md] is available.

## Create mincid master node
There is one mincid master node that control and uses the build
machines.  Do not use the master node as build node.

```
cd ../images
cp --sparse=auto debstretchgi.qcow2 mincid1master.qcow2
```

In the virt-manager create a new VM and chose *Import existing disk
image*.

After starting the VM, set an appropriate hostname. Reboot and login a
root (or have appropriate sudo installed):

```
apt-get install nfs-kernel-server slurmctld slurm-client git docker.io
```

## Create mincid build nodes
You need at least one build node.  It is highly recommended not use
use the master as build node.  Plan the build VMs as you need and give
the appropriate number of cores and memory when setting up the VMs.

```
cd ../images
cp --sparse=auto debstretchgi.qcow2 mincid1build1.qcow2
cp --sparse=auto debstretchgi.qcow2 mincid1build2.qcow2
```

Or tar / sftp to another server.  Import the image as a new VM.

Also here: set an appropriate hostname and reboot.

On all build nodes install

```
apt-get install slurmd slurm-client docker.io
```

## slurm configuration

Please consult the [slurm](https://computing.llnl.gov/linux/slurm/)
site how to configure slurm itself.  For me, the following
configuration works.  Mostly all is the standard configuration -
except the Control[Machine|Addr], NodeName and PartitionName.

```
ControlMachine=mincid1master
ControlAddr=10.0.0.143
AuthType=auth/munge
CacheGroups=0
CryptoType=crypto/munge
MpiDefault=none
ProctrackType=proctrack/pgid
ReturnToService=2
SlurmctldPidFile=/var/run/slurm-llnl/slurmctld.pid
SlurmctldPort=6817
SlurmdPidFile=/var/run/slurm-llnl/slurmd.pid
SlurmdPort=6818
SlurmdSpoolDir=/tmp/slurmd
SlurmUser=slurm
StateSaveLocation=/tmp
SwitchType=switch/none
TaskPlugin=task/none
InactiveLimit=0
KillWait=30
MinJobAge=300
SlurmctldTimeout=120
SlurmdTimeout=300
Waittime=0
FastSchedule=1
SchedulerType=sched/backfill
SchedulerPort=7321
SelectType=select/cons_res
SelectTypeParameters=CR_Core_Memory
AccountingStorageType=accounting_storage/none
AccountingStoreJobComment=YES
ClusterName=cluster
JobCompType=jobcomp/none
JobAcctGatherFrequency=30
JobAcctGatherType=jobacct_gather/none
SlurmctldDebug=3
SlurmdDebug=3
NodeName=mincid1build[1-2] NodeAddr=10.0.0.14[4-5] Sockets=1 CoresPerSocket=2 ThreadsPerCore=1 State=UNKNOWN
PartitionName=mincid Nodes=mincid1build[1-2] Default=YES MaxTime=INFINITE State=UP
```

Also be sure to set the pid file correctly (see the service definition
of slurm(ctl)d.service).  If not systemd might fail
to start up the service.

### Check slurm(ctl)d configuration
Copy the configuration to all nodes (to the directory: /etc/slurm-llnl)

On the master node run

```
slurmctld -Dvvvv
```

On the client nodes run

```
slurmd -Dvvvv
```

Check with

```
sinfo
```

if all nodes are connected.

Because of a problem with systemd and slurm(ctl)d, there is a need to
adapt the [tbc]