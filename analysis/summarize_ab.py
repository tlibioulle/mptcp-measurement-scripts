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
import csv, pickle

parser = argparse.ArgumentParser(
    description="Analyze curl-experiments using MPTCP with different topologies factors")
parser.add_argument("-d",
                    "--directory", help="directory where there are pcap files")
parser.add_argument("-s",
                    "--subdirectory", default=0, help="number of subdirectory to analyze")
parser.add_argument("-c",
                    "--csv-file", help="Output stat csv file name")
parser.add_argument("-S",
                    "--sender", help="sender : client or server ?")

args = parser.parse_args()

direct = os.path.abspath(os.path.expanduser(args.directory))

def template_csv(csv_file):
    csv_file_writer = csv.writer(csv_file,delimiter=',',
                           quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_file_writer.writerow(['capacity_1','delay_1','queue_1','capacity_2','delay_2','queue_2' \
                            ,'filesize', 'total_time', 'complete_r', \
                            'total_trans', 'HTML_trans','connect_mean', \
                            'process_mean', 'waiting_mean', 'total_mean' \
                            ])
    return csv_file_writer

def aggregate_stats(csv_file, directory, sender, min_depth=0 , max_depth=0):
    """ Enter subdirectory and analyze stats files """
    if os.path.isdir(directory):
        i = 0
        for dirpath, dirnames, filename in os.walk(directory):                
            if i >= min_depth and i <= max_depth:
                for dirname in dirnames:
                    if i <= max_depth:
                        analyze_stats(csv_file, os.path.join(dirpath, dirname), sender)
                        print dirname
                    i = i + 1
            else:
                if i > max_depth:
                    break
                else:
                    i = i + 1

def analyze_stats(csv_file, directory, sender):
    """ Analyze stats file and write in csv """
    if os.path.isdir(directory):
        i = 0
        for dirpath, dirnames, filename in os.walk(directory):                
            for dirname in dirnames:
                s = dirname.split('-')
                if len(s) != 2:
                    continue
                else:
                    topo_1 = s[0].split('_')
                    topo_2 = s[1].split('_')
                    name = os.path.join(directory, dirname)
                    name = os.path.join(name, 'ab_' + str(sender) + '.log')
                    to_write = [0]*15
                    to_write[0:3] = topo_1
                    to_write[3:6] = topo_2
                    
                    with open(name,'rb') as analyzed_file:
                        for line in analyzed_file:
                            line = line.replace('\t',' ')
                            
                            parse_line(line, to_write)
                                
                    csv_file.writerow(to_write)

def parse_line(line, to_write):
    s = line.split(":")
    stat_name = s[0]
    if stat_name == "Document Length":
        stat = s[1].replace("bytes",'').replace(" ",'').replace("\n",'')
        to_write[6] = str(int(stat))
    elif stat_name == "Time taken for tests":
        stat = s[1].replace("seconds","").replace(" ","").replace("\n",'')
        time = float(stat)
        time = time if time < 100.0 else time/1000.0
        to_write[7] = str(time)
    elif stat_name == "Complete requests":
        stat = s[1].replace(" ","").replace("\n",'')
        to_write[8] = str(int(stat))
    elif stat_name == "Total transferred":
        stat = s[1].replace("bytes","").replace(" ","").replace("\n",'')
        to_write[9] = str(int(stat))
    elif stat_name == "HTML transferred":
        stat = s[1].replace("bytes","").replace(" ","").replace("\n",'')
        to_write[10] = str(int(stat))
    elif stat_name == "Connect":
        stats = s[1].split(" ")
        i = 0
        for stat in stats:
            if not stat == '':
                if i == 1:
                    to_write[11] = str(int(stat))
                    break
                i += 1
    elif stat_name == "Processing":
        stats = s[1].split(" ")
        i = 0
        for stat in stats:
            if not stat == '':
                if i == 1:
                    to_write[12] = str(int(stat))
                    break
                i += 1
    elif stat_name == "Waiting":
        stats = s[1].split(" ")
        i = 0
        for stat in stats:
            if not stat == '':
                if i == 1:
                    to_write[13] = str(int(stat))
                    break
                i += 1
    elif stat_name == "Total":
        stats = s[1].split(" ")
        i = 0
        for stat in stats:
            if not stat == '':
                if i == 1:
                    to_write[14] = str(int(stat))
                    break
                i += 1

csv_filename = args.csv_file
sender = args.sender

csvfile = open(csv_filename, 'w')
csv_file_writer = template_csv(csvfile)
aggregate_stats(csv_file_writer, direct, sender, 0, int(args.subdirectory)-1)

csvfile.close()
