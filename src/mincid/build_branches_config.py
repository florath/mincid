#!/usr/bin/env python3
#
# Executed within sbatch

from MLogger import MLogger

import os
import sys
import json
import subprocess

class BranchesConfig(object):

    def __init__(self, tmp_dir):
        self.__tmp_dir = tmp_dir
        self.__working_dir = os.path.join(self.__tmp_dir, ".mincid")
        self.__logger = MLogger("BranchesConfig", "BC", self.__working_dir)

        with open(os.path.join(self.__working_dir, "project_config.json"), "r") as fd:
            self.__config = json.load(fd)
        with open(os.path.join(self.__working_dir, "mincid_master.json"), "r") as fd:
            self.__master_config = json.load(fd)

        self.__logger.info("Init branches config")

    def process(self):
        self.__logger.info("Start branches config")

        self.__logger.debug("Get branch config")
        stdouterr_filename = os.path.join(self.__working_dir,
                                          "docker_build_branches.stdouterr")
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(["docker", "run", "--rm=true", "-i",
                                  "-v", "%s:/working:rw" % self.__working_dir,
                                  self.__master_config['worker_image'],
                                  "/bin/bash"], stdin=subprocess.PIPE,
                                 stdout=fd_stdouterr, stderr=fd_stdouterr)
        p.stdin.write(bytes(
"""%s
su - builder --command "%s"
su - builder --command 'git clone %s %s'
""" % ("\n".join(self.__master_config['imagedef'][self.__master_config['worker_image']]['setup_image_minimalistic']),
       self.__config['vcs']['authcmd'], self.__config['vcs']['url'],
       self.__config['dest']), "UTF-8"))

        for branch_name in self.__config['branches']:
            name_for_fs = branch_name.replace("/", "_")

            p.stdin.write(bytes(
"""su - builder --command 'cd %s && git checkout %s && mkdir -p /working/%s && cp %s /working/%s/mincid.json && chmod -R a+rwX /working/%s'
""" %(self.__config['dest'], branch_name, name_for_fs, self.__config['config'], name_for_fs,
      name_for_fs), 'UTF-8'))

        p.stdin.close()
        p.wait()
        self.__logger.debug("Docker process return value [%d]" % p.returncode)

        if p.returncode != 0:
            # Exit with the result of the docker (script) if not successfull
            sys.exit(p.returncode)

        # At this point for each branch there is a directory (in the tmp dir)
        # that contains the configuration for the appropriate branch.
        # Now start up the jobs (one for each branch) to handle these.
        for branch_name in self.__config['branches']:
            # Create Branch dir
            dirname = os.path.join(self.__working_dir,
                                   branch_name.replace("/", "_"))
            stdouterr_filename = os.path.join(dirname, "sbatch.stdouterr")
            with open(stdouterr_filename, "w") as fd_stdouterr:
                p = subprocess.Popen(
                    ["sbatch", "--job-name=Branch_%s" %
                     branch_name,
                     "--export=PYTHONPATH",
                     os.path.join(self.__master_config['mincid_install_dir'],
                                  "build_branch.py"), branch_name,
                     self.__tmp_dir],
                    stdout=fd_stdouterr, stderr=fd_stdouterr)
                p.wait()
            self.__logger.info("sbatch process return value [%d]" %
                               p.returncode)
            self.__logger.info("Finished branch startup [%s]" % branch_name)
        self.__logger.info("Finished complete branch startup")
  
def main():
    bc = BranchesConfig(sys.argv[1])
    bc.process()

if __name__=="__main__":
    main()
