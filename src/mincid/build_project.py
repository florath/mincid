#!/usr/bin/env python3
#
# Handles one project (reads the config from the config file)
# and starts up the jobs that handle the branches.
#
import sys

from mincid.Project import Project

def main(master_cfg, project_cfg):
    project = Project(master_cfg, project_cfg)
    project.cleanup()
    project.process()

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2])
