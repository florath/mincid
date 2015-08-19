#!/usr/bin/env python3

from MLogger import MLogger
from Config import Config

import os
import re
import sys
import json
import subprocess

class Variant(object):

    def __init__(self, cfgfile):
        with open(cfgfile, "r") as fd:
            self.__lconfig = json.load(fd)
        with open(
                os.path.join(self.__lconfig['global_tmp_dir'],
                             'project_config.json'), "r") as fd:
            self.__global_config = json.load(fd)
        with open(os.path.join(self.__lconfig['global_tmp_dir'],
                               "mincid_master.json"), "r") as fd:
            self.__master_config = json.load(fd)

        self.__config = Config(self.__lconfig['global_tmp_dir'],
                               self.__lconfig['branch_name'])
            
        self.__name = self.__lconfig['name']
        self.__variant_dir = self.__lconfig['directory']
        self.__logger = MLogger("Variant", self.__name, self.__variant_dir)
        self.__logger.info("Init variant [%s]" % self.__lconfig['name'])

        self.__cmds = []
        self.__build_pre_cmds = [r'true']
        self.__cmds_post = [r'true']

    def __variant_cmds(self, variant_flat):
        # Check if re matches
        for vcfg in self.__master_config['imagedef'][self.__lconfig['base']]['variant_cmds']:
            vre = vcfg[0]
            vcmd = vcfg[1]
            self.__logger.debug("RE search [%s] [%s]" % (vre, variant_flat))
            result = re.search(vre, variant_flat)
            if not result:
                continue
            for icmd in vcmd:
                self.__logger.info("Calling Sub [%s] [%s] [%s]" %
                                   (vre, icmd, variant_flat))
                nsub = re.sub(vre, icmd, variant_flat)
                self.__logger.info("Add cmd [%s]" % nsub)
                self.__cmds.append(nsub)

            if len(vcfg)>2:
                vpreb = vcfg[2]
                for ipreb in vpreb:
                    self.__logger.info("Calling Sub [%s] [%s] [%s]"
                                       % (vre, ipreb, variant_flat))
                    nsub = re.sub(vre, ipreb, variant_flat)
                    self.__logger.info("Add pre cmd [%s]" % nsub)
                    self.__build_pre_cmds.append(nsub)

    def __variant_install_pkgs(self, install_dict):
        # Add other packages...
        pkgs=[]
        if not 'pkgs' in install_dict:
            return

        rpkgs = self.__config.expand(install_dict['pkgs'])

        install_pkg_names = self.__master_config['imagedef'][self.__lconfig['base']]['pkg_names']
        for ipkg in rpkgs:
            if not ipkg in install_pkg_names:
                self.__logger.warning(
                    "Package with symolic name [%s] " % ipkg
                    + "has no name mapping")
                pkgs.append(ipkg)
            else:
                pkgs.extend(install_pkg_names[ipkg])
        if len(pkgs)>0:
            self.__cmds.append(
                "%s %s" % (
                    self.__master_config['imagedef'][self.__lconfig['base']]['install_pkg_cmd'],
                    (" ".join(pkgs))))

    def __variant_cmds_post(self, install_dict):
        # Add packages from the control file
        # Please note that this can happen AFTER the checkout!
        if not 'control_files' in install_dict:
            self.__logger.info("No control files given")
            return
            
        for cf in install_dict['control_files']:
            self.__logger.info("Control file [%s]" % cf)
            self.__cmds_post.append(
                "cd ~builder && mk-build-deps "
                + "--tool='apt-get -y --no-install-recommends' "
                + "--install %s" % cf)

    def __variant_prepare(self):
        if not 'prepare' in self.__lconfig:
            self.__logger.info("No prepare given")
            return
        self.__cmds.extend(self.__lconfig['prepare'])
            
    def __handle_variant(self):
        variant_flat = ":" + ":".join(self.__lconfig['variant_list']) + ":"
        self.__logger.info("Flat variant [%s]" % variant_flat)

        self.__variant_prepare()
        self.__variant_cmds(variant_flat)
    
    def process(self):
        self.__logger.info("Start variant [%s]" % self.__name)

        if 'variant_list' in self.__lconfig:
            self.__handle_variant()
        self.__variant_install_pkgs(self.__lconfig['install'])
        self.__variant_cmds_post(self.__lconfig['install'])
                
        stdouterr_filename = os.path.join(
            self.__variant_dir, "docker.stdouterr")
        rm_docker_image = "true"
        if "remove_docker_image" in self.__master_config['imagedef'][self.__lconfig['base']]:
            rm_docker_image =  self.__master_config['imagedef'][self.__lconfig['base']]['remove_docker_image']
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(
                ["docker", "run", "--rm=%s" % rm_docker_image, "-i",
                 "-v", "%s:/artifacts:rw" % self.__lconfig['global_tmp_dir'],
                 self.__lconfig['base'],
                 "/bin/bash", "-x", "-e"], stdin=subprocess.PIPE,
                stdout=fd_stdouterr, stderr=fd_stdouterr)
        p.stdin.write(bytes(
"""%s
%s
su - builder --command "%s"
su - builder --command 'git clone %s %s'
su - builder --command 'cd %s && git checkout %s'
%s
su - builder --command '%s && %s'""" %
            ("\n".join(self.__master_config['imagedef'][self.__lconfig['base']]['setup_image']),
             " && ".join(self.__cmds),
              self.__global_config['vcs']['authcmd'],
              self.__global_config['vcs']['url'],
              self.__global_config['dest'], self.__global_config['dest'],
              self.__lconfig['branch_name'], " && ".join(self.__cmds_post),
              " && ".join(self.__build_pre_cmds),
              self.__lconfig['run']), 'UTF-8'))
        
        p.stdin.close()
        p.wait()
        self.__logger.info("Docker process return value [%d]" % p.returncode)
        self.__logger.info("Finished variant [%s]" % (self.__name))
        # Exit with the result of the docker (script)
        sys.exit(p.returncode)

def main():
    variant = Variant(sys.argv[1])
    variant.process()

if __name__=="__main__":
    main()


