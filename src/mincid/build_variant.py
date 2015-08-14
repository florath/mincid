#!/usr/bin/env python3

class Deprecated(object):

    def __variant_cmds(self, variant_flat):
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
                self.__logger.info("Calling Sub [%s] [%s] [%s]" %
                                   (vre, icmd, variant_flat))
                nsub = re.sub(vre, icmd, variant_flat)
                self.__logger.info("Add cmd [%s]" % nsub)
                cmds.append(nsub)

            if len(vcfg)>2:
                vpreb = vcfg[2]
                for ipreb in vpreb:
                    self.__logger.info("Calling Sub [%s] [%s] [%s]"
                                       % (vre, ipreb, variant_flat))
                    nsub = re.sub(vre, ipreb, variant_flat)
                    self.__logger.info("Add pre cmd [%s]" % nsub)
                    build_pre_cmds.append(nsub)
        return cmds, build_pre_cmds

    def __variant_install_pkgs(self, install_dict, cmds):
        # Add other packages...
        pkgs=[]
        if not 'pkgs' in install_dict:
            return
            
        for ipkg in install_dict['pkgs']:
            if not ipkg in INSTALL_PKG_NAMES:
                self.__logger.warning("Package with symolic name [%s] "
                                      + "has no name mapping" % ipkg)
                pkgs.append(ipkg)
            else:
                pkgs.append(INSTALL_PKG_NAMES[ipkg])
        if len(pkgs)>0:
            cmds.append("apt-get -y install --no-install-recommends %s" %
                        (" ".join(pkgs)))

    def __variant_cmds_post(self, install_dict, cmds):
        # Add packages from the control file
        # Please note that this can happen AFTER the checkout!
        cmds_post=[]
        if not 'control_files' in install_dict:
            return
            
        cmds.append("apt-get -y install --no-install-recommends equivs")
        for cf in install_dict['control_files']:
            cmds_post.append("cd ~builder && mk-build-deps "
                             + "--tool='apt-get -y --no-install-recommends' "
                             + "--install %s" % cf)
        return cmds_post

    def __start_variant(self, sname, image, variant_list):
        self.__logger.info("Start variant [%s] [%s] [%s]"
                           % (sname, image, variant_list))

        variant_flat = ":" + ":".join(variant_list) + ":"
        self.__logger.info("Flat variant [%s]" % variant_flat)

        cmds, build_pre_cmds = self.__variant_cmds(variant_flat)
        self.__variant_install_pkgs(image['install'], cmds)

        cmds_post = self.__variant_cmds_post(image['install'], cmds)
                
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

        
        self.__logger.info("Finished variant [%s] [%s] [%s]"
                           % (sname, image, variant_list))
