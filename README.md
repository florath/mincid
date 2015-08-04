# mincid
Minimalistic Countinous Integration &amp; Delivery Tool

## Introduction
There are a lot of different Continous Integration and Continous
Delivery tools around.  [Jenkins](https://jenkins-ci.org/) might be
the most known and used.

IMHO mostly all of these tools are too big and they do not exactly do
what I want.

For the last two years I used Jenkins in my every day's job - but it
does only 80% of that what I want.  There might plugins for
the missing features - but the many many plugins and the interactions
between them are the major source of problems.

After that I had a short look at
(gitlab-ci)[https://about.gitlab.com/gitlab-ci/] and (go
cd)[http://www.go.cd/].  gitlab-ci looks good, but miss some features
that I miss.  After installing the gocd package (143MByte) the
server was not reachable: no sensible logs.  Did you try to debug such
a beast?

Therefore I started over starting with something small and usable.

## Requirements
**mincid** should
* build projects
* be able to build projects on different variants (e.g. different
  compilers, different libraries, different java implementations, ...)
* start each build in a separated environment
  Docker is used
* use an easy text file based configuration
  Maybe: JSON based and stored in a git repo
* use an easy notification mechanism (in case of a problem)
  Maybe: EMail and IRC
* provide easy access to artifacts and log files
  Maybe: NFS export
* (Optional) provide statistics information to a Carbon / Graphite
  instance

## Anti-Requirements
There are some *not* requirements - things **mincid** will never
implement:
* GUI
* Millions of plugins and modules
* Complex structure

## Stay tuned
more (source code) to come....
