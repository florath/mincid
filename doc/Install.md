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

### Download Installation Image
Download from [Debian Web Site](https://www.debian.org/CD/http-ftp/)

### Install VM
We will use the virt-maganger.  Start it up and click 'new VM'.

![Virt-Manager New VM 1](./images/NewVM1.png?raw=true)

Press *Forward* and browse for the ISO image and select *Linux* and
*Debian Wheezy*.

![Virt-Manager New VM 2](./images/NewVM2.png?raw=true)

Press *Forward*.  On the next dialog chose the basic hardware setup
(memory / CPUs) for the golden image.  1GByte RAM and one or two CPU
cores should be enough.

![Virt-Manager New VM 3](./images/NewVM3.png?raw=true)

Press *Forward*.  Depending on your preferences, you need to chose a
disk size and location here.  I prefer to have a separate disk for VM
images.  The size for the pure golden image needs not be larger than
8GBytes.

![Virt-Manager New VM 4](./images/NewVM4.png?raw=true)

Give the machine a name and *Forward*.

![Debian Installation Begin](images/DebInstallBegin.png?raw=true)

Continue installation of the Debian System.  Chose LVM for disk: this
gives the possibility to easy enlarge the disk image later on.
Only minimal set of packages need to be chosen (ssh server and
standard system utilities).

![Debian Installation Packets](images/DebInstallPackets.png?raw=true)

After the reboot, directly halt the VM.  This image is now used to set
up the other machines.

## Create mincid master node
There is one mincid master node that control and uses the build
machines.  Do not use the master node as build node.

```
cd ../images
cp --sparse=auto debstretchgi.qcow2 mincid1master.qcow2
```

In the virt-manager create a new VM and chose *Import existing disk
image*.

