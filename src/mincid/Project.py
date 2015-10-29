#
# Class representing one project
# with all possible branches.
#

import os
import json
import time
import shutil
import tempfile
import subprocess

from mincid.lib.MLogger import MLogger
from mincid.lib.RFSString import RFSString

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

    def cleanup(self):
        """Cleanup: removes old builds"""
        bdir = os.path.join(
            self.__master_config["worker_dir"],
            self.__rfs.fs())
        ldirs = os.listdir(bdir)
        # Check if there is something to do.
        mbuild_cnt = int(self.__config['max_build_cnt'])
        if len(ldirs) < mbuild_cnt:
            self.__logger.info("Nothing to remove: should store [%d] existent [%d]"
                               % (mbuild_cnt, len(ldirs)))
            return
        sldirs = sorted(ldirs)
        while len(sldirs) >= mbuild_cnt:
            self.__logger.info("Removing old build [%s]" % sldirs[0])
            shutil.rmtree(os.path.join(bdir, sldirs[0]))
            del sldirs[0]
        
    def process(self):
        self.__logger.info("Start project [%s]" % self.__name)
        stdouterr_filename = os.path.join(self.__working_dir,
                                          "sbatch_project.stdouterr")
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(
                ["sbatch", "--job-name=%s+BranchesConfig" % self.__name,
                "--output=%s" % os.path.join(self.__working_dir,
                                             "slurm_build_project_%j.out"),
                 "--export=PYTHONPATH",
                 os.path.join(self.__master_config['mincid_install_dir'],
                              "build_branches_config.py"), self.__tmp_dir],
                stdout=fd_stdouterr, stderr=fd_stdouterr)
        p.wait()
        self.__logger.info("sbatch process return value [%d]" % p.returncode)
        self.__logger.info("Finished project startup [%s]" % self.__name)
