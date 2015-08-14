#!/usr/bin/env python3
#
# Executed within sbatch

from MLogger import MLogger

import os
import sys
import json
import subprocess

WORKER_IMAGE="debian9"

class BranchesConfig(object):

    def __init__(self, tmp_dir):
        self.__tmp_dir = tmp_dir
        self.__logger = MLogger("BranchesConfig", "BC", self.__tmp_dir)

        with open(os.path.join(self.__tmp_dir, "project_config.json"), "r") as fd:
            self.__config = json.load(fd)

        self.__logger.info("Init branches config")

    def process(self):
        self.__logger.info("Start branches config")

        self.__logger.debug("Get branch config")
        stdouterr_filename = os.path.join(self.__tmp_dir, "docker_build_branches.stdouterr")
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(["docker", "run", "--rm=true", "-i",
                                  "-v", "%s:/artifacts:rw" % self.__tmp_dir,
                                  WORKER_IMAGE,
                                  "/bin/bash"], stdin=subprocess.PIPE,
                                 stdout=fd_stdouterr, stderr=fd_stdouterr)
        p.stdin.write(bytes(
"""chmod a+rwx /artifacts
useradd --create-home builder
su - builder --command "%s"
su - builder --command 'git clone %s %s'
""" % (self.__config['vcs']['authcmd'], self.__config['vcs']['url'],
       self.__config['dest']), "UTF-8"))

        for branch_name in self.__config['branches']:
            name_for_fs = branch_name.replace("/", "_")

            p.stdin.write(bytes(
"""su - builder --command 'cd %s && git checkout %s && mkdir -p /artifacts/%s && cp mincid.json /artifacts/%s/mincid.json && chmod -R a+rwX /artifacts/%s'
""" %(self.__config['dest'], branch_name, name_for_fs, name_for_fs, name_for_fs), 'UTF-8'))

        p.stdin.close()
        p.wait()
        self.__logger.debug("Docker process return value [%d]" % p.returncode)

        # At this point for each branch there is a directory (in the tmp dir)
        # that contains the configuration for the appropriate branch.
        # Now start up the jobs (one for each branch) to handle these.
        for branch_name in self.__config['branches']:
            # Create Branch dir
            dirname = os.path.join(self.__tmp_dir, branch_name.replace("/", "_"))
            stdouterr_filename = os.path.join(dirname, "sbatch.stdouterr")
            with open(stdouterr_filename, "w") as fd_stdouterr:
                p = subprocess.Popen(["sbatch", "--job-name=Branch_%s" % branch_name,
                                      "--export=PYTHONPATH",
                                      os.path.join("/home/mincid/devel/mincid/src/mincid",
                                                   "build_branch.py"), branch_name, self.__tmp_dir],
                                     stdout=fd_stdouterr, stderr=fd_stdouterr)
                p.wait()
            self.__logger.info("sbatch process return value [%d]" % p.returncode)
            self.__logger.info("Finished branch startup [%s]" % branch_name)
        self.__logger.info("Finished complete branch startup")
  
def main():
    bc = BranchesConfig(sys.argv[1])
    bc.process()

if __name__=="__main__":
    main()
