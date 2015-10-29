#!/usr/bin/env python3
#

from mincid.lib.MLogger import MLogger
from mincid.lib.Config import Config
from mincid.lib.RFSString import RFSString

import os
import sys
import json
import tempfile
import itertools
import subprocess

class Branch(object):

    def __init__(self, branch_name, tmp_dir):
        self.__name = branch_name
        self.__tmp_dir = tmp_dir
        self.__working_dir = os.path.join(self.__tmp_dir, ".mincid")
        
        with open(os.path.join(self.__working_dir, "mincid_master.json"), "r") as fd:
            self.__master_config = json.load(fd)

        self.__jobids = {}
        self.__config = Config(self.__working_dir, branch_name)
        self.__branch_dir = os.path.join(self.__working_dir,
                                         branch_name.replace("/", "_"))
        self.__logger = MLogger("Branch", "build_branch", self.__branch_dir)
        self.__logger.info("Init branch [%s]" % (self.__name))
        self.__variants_base_dir = os.path.join(self.__branch_dir, "variants")
        os.makedirs(self.__variants_base_dir)

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
        base = self.__config.expand(image['base'])
        self.__logger.info("Start variant [%s] [%s] [%s]"
                           % (sname, base, variant_list))
        stdouterr_filename = os.path.join(self.__branch_dir,
                                          "start_variants.stdouterr")

        dep_jobids = []
        # Collect jobids of all dependend stages
        if 'depends_on' in self.__config.branch_jobs()[sname]:
            for dep_stage in self.__config.branch_jobs()[sname]['depends_on']:
                dep_jobids.extend(self.__jobids[dep_stage])
            self.__logger.info("Dependent jobids [%s]" % dep_jobids)
        
        with open(stdouterr_filename, "w") as fd_stdouterr:
            # Create own temp dir
            rfsname = RFSString(self.__name)
            rfsbase = RFSString(base)
            variant_name = "%s+%s+%s+%s+%s" % \
                           (self.__config.project_cfg('name'),
                            rfsname.fs(),
                            sname, rfsbase.fs(), "_".join(variant_list))
            variant_tmp_dir = os.path.join(self.__variants_base_dir, variant_name)
            os.makedirs(variant_tmp_dir, exist_ok=True)
            variant_desc = {
                'name': variant_name,
                'base': base,
                'branch_name': self.__name,
                'global_tmp_dir': self.__tmp_dir,
                'directory': variant_tmp_dir
            }

            if len(variant_list)>0:
                variant_desc['variant_list'] = variant_list

            for pword in ('install', 'run'):
                if pword in self.__config.branch_jobs()[sname]:
                    variant_desc[
                        pword] = self.__config.branch_jobs()[sname][pword]

            if 'prepare' in image:
                variant_desc['prepare'] = image['prepare']
                
            if 'build_prepare' in image:
                variant_desc['build_prepare'] = image['build_prepare']

            variant_cfg_file_name = os.path.join(
                variant_tmp_dir, "variant.json")
            with open(variant_cfg_file_name, "w") as fd:
                json.dump(variant_desc, fd)

            subproc_slist = [
                "sbatch", "--job-name=%s" % variant_name,
                "--output=%s" % os.path.join(self.__working_dir,
                                             "slurm_build_branch_%j.out"),
                "--extra-node-info=1:2:1",
                 "--export=PYTHONPATH"]
            if len(dep_jobids)>0:
                dep_str = ":".join(str(x) for x in dep_jobids)
                self.__logger.info("New batch is dependent on [%s]" %
                                   dep_str)
                subproc_slist.append("--dependency=afterok:%s" % dep_str)
            subproc_slist.extend(
                [os.path.join(self.__master_config['mincid_install_dir'],
                              "build_variant.py"), variant_cfg_file_name])
                
            p = subprocess.Popen(subproc_slist,
                stdout=subprocess.PIPE, stderr=fd_stdouterr)

        res = p.stdout.read()
        p.wait()
        
        self.__logger.info("sbatch process return value [%d]" % p.returncode)

        decoded = res.decode("UTF-8")
        jobnr = int(decoded[20:-1])
        self.__jobids[sname].append(jobnr)
        
        self.__logger.info("sbatch process id [%d]" % jobnr)
        self.__logger.info("Finished variant [%s] [%s] [%s]"
                           % (sname, base, variant_list))
    
    def __start_variants(self, sname, image):
        self.__logger.info("Start variants [%s] [%s]" % (sname, image))
        variants = list(itertools.product(*image['variants']))
        for variant_list in variants:
            self.__start_variant(sname, image, variant_list)
        self.__logger.info("Finished variants [%s] [%s]" % (sname, image))

    def __start_image(self, sname, image):
        jc = self.__config.branch_jobs()
        base = self.__config.expand(image['base'])
        if 'ignore' in image and image['ignore']=="true":
            self.__logger.info("Ignoring image [%s] [%s]" % (sname, base))
            return
        self.__logger.info("Start image [%s] [%s]" % (sname, base))
        if 'variants' in image:
            self.__start_variants(sname, image)
        else:
            self.__start_variant(sname, image, [])
            
        self.__logger.info("Finished image [%s] [%s]" % (sname, base))

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
