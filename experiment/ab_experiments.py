################################
#           IMPORTS            #
################################

import csv
import argparse
import os
import os.path
import sys
import time
from datetime import datetime
from subprocess import call
from shutil import copyfile
import common as co

################################
#         PARSE ARGS           #
################################

parser = argparse.ArgumentParser(
    description="Experiments MPTCP with different topologies factors")
parser.add_argument("-p",
                    "--mpperf-file", help="directory/file of the minitopo mpPerf script")
parser.add_argument("-t",
                    "--topo-base", help="file with the base topology")
parser.add_argument("-x",
                    "--xp-base", help="file with the base experiment")
parser.add_argument("-d",
                    "--res-dir", help="directory where the results of the experiments will be stored")
parser.add_argument("-e",
                    "--experiments", help="csv file with the different factors of the experimental design")
parser.add_argument("-T",
                    "--timeout", help="Apache bench timelimit")
parser.add_argument("-s",
                    "--sizes", help="file sizes")
parser.add_argument("-o",
                    "--only-one-path", action='store_true', help="Use only one path")

args = parser.parse_args()

dir_exp = os.path.abspath(os.path.expanduser(args.res_dir))
topo_file = os.path.abspath(os.path.expanduser(args.topo_base))
xp_base = os.path.abspath(os.path.expanduser(args.xp_base))

bin_mpPerf = os.path.abspath(os.path.expanduser(args.mpperf_file))
experiment_file = os.path.abspath(os.path.expanduser(args.experiments))

sizes = args.sizes.split(',')

def launch_experiments(exp_factors):
	""" Create the xp file and lauch the different experiments """
    #create directory
    dir_name = datetime.now().strftime('%Y%m%d_%H%M%S')
    dir_path = os.path.join(dir_exp, dir_name)
    co.check_directory_exists(dir_path)

    #save sysctl into a file all dir?
    sysctlerr = os.system('sysctl -a > '+ os.path.join(dir_path, 'sysctl')) 
    sysctlerr = os.system('dmesg | grep MPTCP >> '+os.path.join(dir_path, 'sysctl'))

    for i in range(len(sizes)):
        xp_file = os.path.join(dir_path, 'xp_'+str(i))
	
        copyfile(xp_base,xp_file)
        with open(xp_file, 'a') as xp:
            xp.write(co.HTTP_FILE+':random\n')
            xp.write(co.HTTP_FILESIZE+':'+str(sizes[i])+'\n')
            xp.write(co.AB_TIMELIMIT+':'+str(args.timeout)+'\n')

    for factor in exp_factors:
        for i in range(len(sizes)):
            xp_file = os.path.join(dir_path, 'xp_'+str(i))
            dir_expe = os.path.join(dir_path, 'xp_filesize_'+str(sizes[i]))
            if not args.only_one_path:
                co.experiment_one_topo(factor, dir_expe, xp_file)
            else:
                co.experiment_one_topo_one_path(factor, dir_expe, xp_file)

def open_experiments_csv(exp_csv_file):
	""" Open the file with the different factors of the experimental design """
    factors = list()
    with open(exp_csv_file) as expcsvfile:
        reader = csv.DictReader(expcsvfile)
        i = 0
        for row in reader:
            factors.append(row)
    
    launch_experiments(factors)

open_experiments_csv(experiment_file)
