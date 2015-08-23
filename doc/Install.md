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

![Virt-Manager New VM 1](./images/NewWM1.png?raw=true)

Press *Forward* and browse for the ISO image and select *Linux* and
*Debian Wheezy*.

![Virt-Manager New VM 2](./images/NewWM2.png?raw=true)

