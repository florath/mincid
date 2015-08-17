#!/usr/bin/env python3
#
# Handles one project (reads the config from the config file)
# and starts up the jobs that handle the branches.
#

import os
import sys
import json
import shutil
import tempfile
import subprocess

from MLogger import MLogger

class Project(object):

    def __init__(self, master_conf, desc_file):
        with open(master_conf, "r") as fd:
            self.__master_config = json.load(fd)
        self.__tmp_dir = tempfile.mkdtemp(
            prefix="mincid_build_",
            dir=self.__master_config["worker_dir"])
        shutil.copyfile(desc_file,
                        os.path.join(self.__tmp_dir, "project_config.json"))
        shutil.copyfile(master_conf,
                        os.path.join(self.__tmp_dir, "mincid_master.json"))
        with open(desc_file, "r") as fd:
            self.__config = json.load(fd)
        self.__log_dir = self.__tmp_dir
        self.__name = self.__config['name']
        self.__logger = MLogger("Project", self.__name, self.__log_dir)
        self.__logger.info("Init project [%s]" % self.__name)

    def process(self):
        self.__logger.info("Start project [%s]" % self.__name)
        stdouterr_filename = os.path.join(self.__tmp_dir,
                                          "sbatch_project.stdouterr")
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(
                ["sbatch", "--job-name=BranchesConfig",
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
