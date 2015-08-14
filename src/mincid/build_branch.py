#!/usr/bin/env python3
#

from MLogger import MLogger

import os
import sys

class Branch(object):

    def __init__(self, branch_name, tmp_dir):
        self.__name = branch_name
        self.__tmp_dir = tmp_dir
        self.__branch_dir = os.path.join(tmp_dir, branch_name.replace("/", "_"))
        self.__logger = MLogger("Branch", "build_branch", self.__branch_dir)
        self.__logger.info("Init branch [%s]" % (self.__name))

def main():
    branch = Branch(sys.argv[1], sys.argv[2])
    branch.process()

if __name__=="__main__":
    main()
