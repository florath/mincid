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
        self.__jobids = {}
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

    
    def __start_variant(self, sname, image, variant_list):
        self.__logger.info("Start variant [%s] [%s] [%s]"
                           % (sname, image, variant_list))

        stdouterr_filename = os.path.join(self.__branch_dir,
                                          "start_variants.stdouterr")
        with open(stdouterr_filename, "w") as fd_stdouterr:
            p = subprocess.Popen(
                ["sbatch", "--job-name=Variant_%s_%s" %
                 (image['base'], "_".join(variant_list)),
                 "--export=PYTHONPATH",
                 os.path.join("/home/mincid/devel/mincid/src/mincid",
                              "build_variant.py"), self.__tmp_dir
                 image['base'], "[%s]" % ",".join(variant_list)],
                stdout=fd_stdouterr, stderr=fd_stdouterr)
        p.wait()
        self.__logger.info("sbatch process return value [%d]" % p.returncode)
        self.__logger.info("Finished variant [%s] [%s] [%s]"
                           % (sname, image, variant_list))
    
    def __start_variants(self, sname, image):
        self.__logger.info("Start variants [%s] [%s]" % (sname, image))
        base = image['base']
        variants = list(itertools.product(*image['variants']))
        for variant_list in variants:
            self.__start_variant(sname, image, variant_list)
        self.__logger.info("Finished variants [%s] [%s]" % (sname, image))

    def __start_image(self, sname, image):
        jc = self.__config.branch_jobs()
        self.__logger.info("Start image [%s] [%s]" % (sname, image['base']))
        if 'variants' in image:
            self.__start_variants(sname, image)
        else:
            self.__start_base(sname, image)
            
        self.__logger.info("Finished image [%s] [%s]" %
                           (sname, image['base']))

    def __start_stage(self, sname):
        self.__logger.info("Start stage [%s]" % sname)
        for image in self.__config.branch_jobs()[sname]['images']:
            self.__start_image(sname, image)
        self.__logger.info("Finished stage [%s]" % sname)

    def __start_stages(self, nlist):
        self.__logger.info("Start all stages [%s]" % (nlist))
        # Store all jobids for the appropriate (high level) job
        for n in nlist:
            self.__jobids[n] = []

        for n in nlist:
            self.__start_stage(n)

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
