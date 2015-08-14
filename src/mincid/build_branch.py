#!/usr/bin/env python3
#

from MLogger import MLogger
from Config import Config

import os
import sys

class Branch(object):

    def __init__(self, branch_name, tmp_dir):
        self.__name = branch_name
        self.__tmp_dir = tmp_dir
        self.__config = Config(tmp_dir, branch_name)
        self.__branch_dir = os.path.join(tmp_dir, branch_name.replace("/", "_"))
        self.__logger = MLogger("Branch", "build_branch", self.__branch_dir)
        self.__logger.info("Init branch [%s]" % (self.__name))

    def __sort_deps(self):
        """Sorts the branch jobs using the dependencies"""
        jc = self.__config.branch_jobs()
        result = []
        todo = set(jc.keys())
        while len(todo) > 0:
            for k in todo:
                if not 'depends_on' in jc[k]:
                    # No dependecies: can start right away
                    result.append(k)
                    todo.remove(k)
                    break
                else:
                    don = jc[k]['depends_on']
                    if set(don).issubset(set(result)):
                        # Yep: all dependencies are already handled!
                        result.append(k)
                        todo.remove(k)
                        break
        return result

    def __start_image(self, sname, image, jobids):
        jc = self.__config.branch_jobs()
        self.__logger.info("Start image [%s] [%s]" % (sname, image['base']))
        if 'variants' in image:
            self.__start_variants(sname, image, jobids)
        else:
            self.__start_base(sname, image, jobids)
            
        self.__logger.info("Finished image [%s] [%s]" % (sname, image['base'])

    def __start_stage(self, sname, jobids):
        self.__logger.info("Start stage [%s]" % sname)
        for image in self.__config.branch_jobs()[sname]['images']:
            self.__start_image(sname, image, jobids)
        self.__logger.info("Finished stage [%s]" % sname)

    def __start_stages(self, nlist):
        self.__logger.info("Start all stages [%s]" % (nlist))
        # Store all jobids for the appropriate (high level) job
        jobids = {}
        for n in nlist:
            jobids[n] = []

        for n in nlist:
            self.__start_stage(n, jobids)

        self.__logger.info("Finished stating all stages [%s]" % (nlist))

    def process(self):
        self.__logger.info("Process branch [%s]" % (self.__name))
        nlist = self.__sort_deps()
        self.__logger.info("Node list [%s]" % (nlist))
        self.__start_stages(nlist)
        
def main():
    branch = Branch(sys.argv[1], sys.argv[2])
    branch.process()

if __name__=="__main__":
    main()
