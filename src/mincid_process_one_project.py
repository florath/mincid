#!/usr/bin/python3
#
# Minimalistic Continous Integration & Delivery
#

import re
import os
import sys
import json
import time
import logging
import subprocess
import itertools

# CONFIG

WORKER_IMAGE="debian9"

# Commands that are executed
VC_ALWAYS_PRE=(r"echo 'debconf debconf/frontend select noninteractive' | debconf-set-selections",
               r"echo 'deb-src http://ftp.de.debian.org/debian stretch main' >>/etc/apt/sources.list",
               r"apt-get update",
)

VC_REMOVE_ALL_ALTERNATIVES=r"true"

INSTALL_PKG_NAMES={
}

VARIANT_CMDS = (
    (('.*:g\+\+-([^:]*):.*'),
     (r"apt-get -y install --no-install-recommends g++-\1", ),
     (r'export PLATFORM_COMPILER_NAME=gcc', r'export PLATFORM_CC=/usr/bin/gcc-\1', r'export PLATFORM_CXX=/usr/bin/g++-\1'),
    ),
    (('.*:clang\+\+-([^:]*):.*'),
     (r"apt-get -y install --no-install-recommends clang-\1", ),
     (r'export PLATFORM_COMPILER_NAME=clang', r'export PLATFORM_CC=/usr/bin/clang-\1', r'export PLATFORM_CXX=/usr/bin/clang++-\1')
     ),
    # Do nothing for libstdc++:
    # dependent on the compiler a different lib must be installed
    (('.*:libc\+\+:.*'),
     (r"apt-get -y install --no-install-recommends libc++-dev", ),
     (r'export PLATFORM_CXXLIB_NAME=libc++', )
    ),
    (('.*:g\+\+-([^:]*):.*libstdc\+\+:.*'),
     (r"apt-get -y install --no-install-recommends libstdc++-\1-dev", )),

    # Update alternatives: set /usr/bin/cc and /usr/bin/c++
    (('.*:g\+\+-([^:]*):.*libstdc\+\+:.*'),
     (),
     (r'export PLATFORM_CXXLIB_NAME=libstdc++', ),
    ),
    (('.*:clang\+\+-([^:]*):.*libstdc\+\+:.*'),
     (),
     (r'export PLATFORM_CXXLIB_NAME=libstdc++', ),
    )
)

# CONFIG END

class MLogger(object):

    def __init__(self, name, filename, log_dir):
        try:
            os.makedirs(log_dir)
        except FileExistsError:
            pass
        self.__logger = logging.getLogger(name)
        self.__logger.setLevel(logging.DEBUG)
        self.__log_handler = logging.FileHandler(os.path.join(log_dir, filename + ".log"))
        self.__log_formatter = logging.Formatter(
            '%(asctime)s;%(name)s;%(levelname)s;%(message)s')
        self.__log_handler.setFormatter(self.__log_formatter)
        self.__logger.addHandler(self.__log_handler)

    def __del__(self):
        self.__logger.removeHandler(self.__log_handler)

    def debug(self, msg):
        return self.__logger.debug(msg)

    def info(self, msg):
        return self.__logger.info(msg)

    def warning(self, msg):
        return self.__logger.warning(msg)

    def error(self, msg):
        return self.__logger.error(msg)

class Variant(object):

    def __init__(self, base, vlist, log_dir, global_config, stage_config, branch_name):
        self.__base = base
        self.__name_for_fs = "_".join(vlist)
        self.__vlist = vlist
        self.__log_dir = log_dir
        self.__stage_config = stage_config
        self.__global_config = global_config
        self.__branch_name = branch_name
        self.__logger = MLogger("Variant", self.__name_for_fs, log_dir)
        self.__logger.info("Init variant [%s] [%s]" % (self.__base, self.__name_for_fs))

    def __del__(self):
        self.__logger.info("Del variant [%s]" % (self.__name_for_fs))

    def process(self):
        self.__logger.info("Start variant [%s]" % (self.__name_for_fs))

        variant_flat = ":" + ":".join(self.__vlist) + ":"
        self.__logger.info("Flat variant [%s]" % variant_flat)

        cmds=[]
        build_pre_cmds=[]
        cmds.extend(VC_ALWAYS_PRE)
        # Check if re matches
        for vcfg in VARIANT_CMDS:
            vre = vcfg[0]
            vcmd = vcfg[1]
            self.__logger.debug("RE search [%s] [%s]" % (vre, variant_flat))
            result = re.search(vre, variant_flat)
            if not result:
                continue
            for icmd in vcmd:
                self.__logger.info("Calling Sub [%s] [%s] [%s]" % (vre, icmd, variant_flat))
                nsub = re.sub(vre, icmd, variant_flat)
                self.__logger.info("Add cmd [%s]" % nsub)
                cmds.append(nsub)

            if len(vcfg)>2:
                vpreb = vcfg[2]
                for ipreb in vpreb:
                    self.__logger.info("Calling Sub [%s] [%s] [%s]" % (vre, ipreb, variant_flat))
                    nsub = re.sub(vre, ipreb, variant_flat)
                    self.__logger.info("Add pre cmd [%s]" % nsub)
                    build_pre_cmds.append(nsub)
                
        # Add other packages...
        pkgs=[]
        if 'pkgs' in self.__stage_config['install']:
            for ipkg in self.__stage_config['install']['pkgs']:
                if not ipkg in INSTALL_PKG_NAMES:
                    self.__logger.warning("Package with symolic name [%s] has no name mapping" % ipkg)
                    pkgs.append(ipkg)
                else:
                    pkgs.append(INSTALL_PKG_NAMES[ipkg])
            if len(pkgs)>0:
                cmds.append("apt-get -y install --no-install-recommends %s" % (" ".join(pkgs)))
                
        # Add packages from the control file
        # Please note that this can happen AFTER the checkout!
        cmds_post=[]
        if 'control_files' in self.__stage_config['install']:
            cmds.append("apt-get -y install --no-install-recommends equivs")
            for cf in self.__stage_config['install']['control_files']:
                cmds_post.append("cd ~builder && mk-build-deps --tool='apt-get -y --no-install-recommends' --install %s" % cf)

        self.__logger.debug("Commands [%s]" % (cmds))
                
        stdouterr_filename = os.path.join(self.__log_dir, self.__name_for_fs + ".stdouterr")
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(["docker", "run", "--rm=true", "-i", WORKER_IMAGE,
                                  "/bin/bash", "-x", "-e"], stdin=subprocess.PIPE,
                                 stdout=fd_stdouterr, stderr=fd_stdouterr)
        p.stdin.write(bytes(
"""%s
useradd --create-home builder
su - builder --command "%s"
su - builder --command 'git clone %s %s'
su - builder --command 'cd %s && git checkout %s'
%s
su - builder --command '%s && %s'""" %
            ( " && ".join(cmds),
              self.__global_config['vcs']['authcmd'], self.__global_config['vcs']['url'],
              self.__global_config['dest'], self.__global_config['dest'],
              self.__branch_name, " && ".join(cmds_post),
              " && ".join(build_pre_cmds), self.__stage_config['run']), 'UTF-8'))
        p.stdin.close()
        p.wait()
        self.__logger.info("Docker process return value [%d]" % p.returncode)
        self.__logger.info("Finished variant [%s]" % (self.__name_for_fs))

class Stage(object):

    def __init__(self, name, stage_cfg, global_cfg, log_dir, stage_cnt, branch_name):
        self.__name = name
        self.__log_dir = log_dir
        self.__name_for_fs = "%03d-%s" % (stage_cnt, name)
        self.__stage_config = stage_cfg
        self.__global_config = global_cfg
        self.__branch_name = branch_name
        self.__logger = MLogger("Stage", self.__name_for_fs, log_dir)
        self.__logger.info("Init stage [%s]" % self.__name)

    def __del__(self):
        self.__logger.info("Del stage [%s]" % self.__name)

    def process(self):
        self.__logger.info("Start stage [%s]" % self.__name)
        image_cnt = 0
        for image in self.__stage_config['images']:
            base = image['base']
            self.__logger.info("Start image [%s] [%s]" % (base, image_cnt))
            variants = list(itertools.product(*image['variants']))
            for variant_list in variants:
                variant = Variant(base, variant_list,
                                  os.path.join(self.__log_dir, self.__name_for_fs),
                                  self.__global_config,
                                  self.__stage_config, self.__branch_name)
                variant.process()
                del variant
        self.__logger.info("Finished stage [%s]" % self.__name)
        

class Branch(object):

    def __init__(self, name, cfg, log_dir):
        self.__name = name
        self.__name_for_fs = name.replace("/", "_")
        self.__config = cfg
        self.__log_dir = log_dir
        self.__logger = MLogger("Branch", self.__name_for_fs, log_dir)
        self.__logger.info("Init branch [%s]" % self.__name)

    def __del__(self):
        self.__logger.info("Del branch [%s]" % self.__name)
        
    def __get_branch_config(self):
        self.__logger.debug("Get branch config")
        p = subprocess.Popen(["docker", "run", "--rm=true", "-i", WORKER_IMAGE,
                              "/bin/bash"], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.stdin.write(bytes(
"""useradd --create-home builder
su - builder --command "%s"
su - builder --command 'git clone %s %s'
su - builder --command 'cd %s && git checkout %s 1>&2'
su - builder --command 'cd %s && cat mincid.json'""" %
            (self.__config['vcs']['authcmd'], self.__config['vcs']['url'],
             self.__config['dest'], self.__config['dest'],
             self.__name, self.__config['dest']), 'UTF-8'))
        p.stdin.close()
        out = p.stdout.read()
        for l in p.stderr.readlines():
            self.__logger.error(l)
        p.wait()
        self.__logger.debug("Docker process return value [%d]" % p.returncode)
        self.__logger.debug("Branch config is [%s]" % (out))
        return out
        
    def process(self):
        self.__logger.info("Start branch [%s]" % self.__name)
        branch_cfg = json.loads(self.__get_branch_config().decode("UTF-8"))
        stage_cnt = 0
        for stage_cfg in branch_cfg:
            stage_name = stage_cfg['name']
            stage = Stage(stage_name, stage_cfg, self.__config,
                          os.path.join(self.__log_dir, self.__name_for_fs),
                          stage_cnt, self.__name)
            stage.process()
            stage_cnt += 1
            del stage
        self.__logger.info("Finished branch [%s]" % self.__name)
            
class Project(object):

    def __init__(self, desc_file, log_dir):
        with open(desc_file, "r") as fd:
            self.__config = json.load(fd)
        self.__name = self.__config['name']
        self.__logger = MLogger("Project", self.__name, log_dir)
        self.__logger.info("Init project [%s]" % self.__name)
        self.__log_dir = log_dir

    def __del__(self):
        self.__logger.info("Del project [%s]" % self.__name)

    def process(self):
        self.__logger.info("Start project [%s]" % self.__name)
        for branch_name in self.__config['branches']:
            branch = Branch(branch_name, self.__config,
                            os.path.join(self.__log_dir, self.__name))
            branch.process()
            del branch
        self.__logger.info("Finished project [%s]" % self.__name)

def main():
    project = Project(sys.argv[1], "log")
    project.process()
    del project

if __name__=="__main__":
    main()
