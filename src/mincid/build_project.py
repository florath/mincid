#!/usr/bin/env python3
#
# Handles one project (reads the config from the config file)
# and starts up the jobs that handle the branches.
#

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess

from MLogger import MLogger
from RFSString import RFSString

class Project(object):

    def __init__(self, master_conf, desc_file):
        with open(master_conf, "r") as fd:
            self.__master_config = json.load(fd)
        with open(desc_file, "r") as fd:
            self.__config = json.load(fd)
        self.__name = self.__config['name']
        self.__rfs = RFSString(self.__name)

        self.__tmp_dir = os.path.join(
            self.__master_config["worker_dir"],
            self.__rfs.fs(),
            time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(self.__tmp_dir, exist_ok=True)

        self.__working_dir = os.path.join(self.__tmp_dir, ".mincid")
        os.makedirs(self.__working_dir, exist_ok=True)
        os.chmod(self.__working_dir, 0o777)
            
        shutil.copyfile(desc_file,
                        os.path.join(self.__working_dir, "project_config.json"))
        shutil.copyfile(master_conf,
                        os.path.join(self.__working_dir, "mincid_master.json"))
        self.__logger = MLogger("Project", self.__name, self.__working_dir)
        self.__logger.info("Init project [%s]" % self.__name)

    def process(self):
        self.__logger.info("Start project [%s]" % self.__name)
        stdouterr_filename = os.path.join(self.__working_dir,
                                          "sbatch_project.stdouterr")
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(
                ["sbatch", "--job-name=%s+BranchesConfig" % self.__name,
                 "--export=PYTHONPATH",
                 os.path.join(self.__master_config['mincid_install_dir'],
                              "build_branches_config.py"), self.__tmp_dir],
                stdout=fd_stdouterr, stderr=fd_stdouterr)
        p.wait()
        self.__logger.info("sbatch process return value [%d]" % p.returncode)
        self.__logger.info("Finished project startup [%s]" % self.__name)

def main():
    project = Project(sys.argv[1], sys.argv[2])
    project.process()

if __name__=="__main__":
    main()
