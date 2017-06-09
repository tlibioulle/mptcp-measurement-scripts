################################
#           IMPORTS            #
################################

import argparse
import os
import os.path
import sys
import time
from datetime import datetime
from subprocess import call
from shutil import copyfile

parser = argparse.ArgumentParser(
    description="Experiments MPTCP with different topologies factors")
parser.add_argument("-d",
                    "--directory", help="directory where there are pcap files")
parser.add_argument("-p",
                    "--pcap-file", help="pcap file names")
parser.add_argument("-c",
                    "--config", help="config.py file for mptcp-analyze")
parser.add_argument("-m",
                    "--mptcp-analyze", help="analyze.py the analyze script")
parser.add_argument("-s",
                    "--subdirectory", default=0, help="analyze subdirectory")

args = parser.parse_args()

direct = os.path.abspath(os.path.expanduser(args.directory))

bin_analyze = os.path.abspath(os.path.expanduser(args.mptcp_analyze))

def get_dir_from_arg(directory, end=''):
    """ Get the abspath of the dir given by the user and append 'end' """
    if end.endswith('.'):
        end = end[:-1]

    if directory.endswith('/'):
        directory = directory[:-1]

    return os.path.abspath(os.path.expanduser(directory)) + end

def check_directory_exists(directory):
    """ Check if the directory exists, and create it if needed
        If directory is a file, exit the program
    """
    if os.path.exists(directory):
        if not os.path.isdir(directory):
            print(directory + " is a file: stop")
            sys.exit(1)

    else:
        os.makedirs(directory)

def analyze_dir(directory, min_depth=0 , max_depth=0 ):
    """ Enter subdirectory and analyze pcap files """
    if os.path.isdir(directory):
        i = 0
        for dirpath, dirnames, filename in os.walk(directory):
            if i >= min_depth and i <= max_depth:
                for dirname in dirnames:
                    call([bin_analyze, '-i', os.path.join(dirpath,dirname), '-p', args.pcap_file, '-M'])
                i = i + 1
            else:
                if i > max_depth:
                    break
                else:
                    i = i + 1

if args.subdirectory == 0:
    analyze_dir(direct)
else:
    analyze_dir(direct, 1, args.subdirectory)
