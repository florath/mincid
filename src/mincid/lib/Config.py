
from RFSString import RFSString

import os
import json

class Config(object):

    def __init__(self, base_dir, branch_name):

        self.__branch_name = RFSString(branch_name)

        with open(os.path.join(base_dir, "project_config.json"), "r") as fd:
            self.__project_config = json.load(fd)
        
        with open(os.path.join(base_dir, self.__branch_name.fs(), "mincid.json"), "r") as fd:
            self.__branch_config = json.load(fd)

    def project_cfg(self, key):
        return self.__project_config[key]

    def branch_defines(self, key):
        return self.__branch_config[0][key]

    def branch_jobs(self):
        return self.__branch_config[1]

