################################
#           IMPORTS            #
################################

import argparse
import os
import os.path
import sys
import math
from datetime import datetime
from subprocess import call
from shutil import copyfile
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

parser = argparse.ArgumentParser(
    description="Generate graphs from stats summary")
parser.add_argument("-m",
		"--mptcp", help="CSV file containing MPTCP stats summary")
parser.add_argument("-f",
		"--val-first", help="CSV file containing TCP stats summary")
parser.add_argument("-s",
		"--val-second", help="CSV file containing TCP stats summary")
parser.add_argument("-i",
		"--min", help="CSV file containing TCP stats summary")
parser.add_argument("-x",
		"--max", help="CSV file containing TCP stats summary")
parser.add_argument("-n",
		"--nbr-set", help="CSV file containing TCP stats summary")
parser.add_argument("-p",
		"--plot-dir", help="Directory where the plot are saved")

args = parser.parse_args()

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

dir_plot = args.plot_dir.split(",")

for direct in dir_plot:
	check_directory_exists(direct)

def init_dict(mptcp_s, nbr_set):
    ans = dict()
    for mp in mptcp_s:
        ans[mp] = init_list(nbr_set)
    return ans
    
def init_list(nbr_set):
    ans = list()
    for i in range(0, nbr_set):
        ans.append(list())
    return ans
    
def init_files(mptcp_s):
    fd = list()
    for mp in mptcp_s:
        fd.append(open(mp, 'rb'))
    return fd

def init_summaries(mptcp_fd):
    mptcp = list()
    for mp in mptcp_fd:
        mptcp.append(csv.DictReader(mp))
    return mptcp

def close_files(mptcp_fd):
    for mp in mptcp_fd:
        mp.close()

def compute(row1, row2, results, index, csv_filename, option):
    if option == 'request_per_time':
        ratio1 = float(row1['complete_r'])/float(row1['total_time'])
        ratio2 = float(row2['complete_r'])/float(row2['total_time'])
        res = (ratio1-ratio2)/(ratio1+ratio2)
        results[csv_filename][index].append(res)
        if math.fabs(res) > 0.1 :
            print "path 1 : capacity : " + row1['capacity_1'] + "Mbps, delay : " + row1['delay_1'] + ", queue : " + row1['queue_1'] + "bytes"
            print "path 2 : capacity : " + row2['capacity_2'] + "Mbps, delay : " + row2['delay_2'] + ", queue : " + row2['queue_2'] + "bytes"
            print "ratio : " + str(res)
    else:
        results[csv_filename][index].append((float(row1[option])-float(row2[option]))/(float(row1[option])+float(row2[option])))

def xlabel_name(val):
    name = val.capitalize() + ' difference'
    if val == 'capacity': 
        name = val.capitalize() + ' difference [Mbps]'
    elif val == 'delay':
        name = val.capitalize() + ' difference [ms]'
    elif val == 'queue':
        name = val.capitalize() + ' difference [Packets]'
    return name

def ylabel_name(option):
    name = ''
    if option == 'total_mean':
        name = 'Time taken per request - Ratio'
    elif option == 'waiting_mean':
        name = 'Waiting time per request - Ratio'
    elif option == 'process_mean':
        name = 'Processing time per request - Ratio' 
    elif option == 'connect_mean':
        name = 'Connecting time per request - Ratio'
    elif option == 'complete_r':
        name = 'Completed request - Ratio'
    elif option == 'request_per_time':
        name = 'Completed request per time unit - Ratio'
    return name

def plot_box_mp(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, option, plotfile):

    results = init_dict(csv_mptcp_s, nbr_set)
    
    mptcp_fd = init_files(csv_mptcp_s)
    
    summaries = init_summaries(mptcp_fd)
    
    print option
    for i in range(len(summaries)/2):
        print csv_mptcp_s[2*i]
        for row1, row2 in zip(summaries[2*i],summaries[2*i+1]):
            diff = 0
            index = 0
		
            if min_diff < 0:
                diff = int(row1[val_diff_1])-int(row1[val_diff_2])
            else:
                diff = int(math.fabs(int(row1[val_diff_1])-int(row1[val_diff_2])))
            
            index = (diff-min_diff)*nbr_set/(max_diff-min_diff)
            
            compute(row1, row2, results, index, csv_mptcp_s[2*i], option)

	
    for i in range(len(summaries)/2):
        x_names = []
        x_numbers = []
        l = 1
        o = float(max_diff-min_diff)/float(nbr_set)
        data = []
        for j in range(nbr_set):
            data.append(results[csv_mptcp_s[2*i]][j])
            x_numbers.append(l)
            if j == 0:
                x_names.append("[" + str(int(min_diff)) + "," + str(int(min_diff + (j+1)*o)) + "]")
            elif j == nbr_set-1:
                x_names.append("]" + str(int(min_diff + j*o)) + "," + str(max_diff) + "]")
            else:
                x_names.append("]" + str(int(min_diff + j*o)) + "," + str(int(min_diff + (j+1)*o)) + "]")
            l += 1
        
        fig = plt.figure()
        plt.xlabel(xlabel_name(val_diff_1[:-2]))
        plt.ylabel(ylabel_name(option))
        
        plt.boxplot(data)
        
        plt.xticks(range(1,nbr_set+1),range(min_diff+(max_diff-min_diff)/nbr_set,max_diff+(max_diff-min_diff)/nbr_set,(max_diff-min_diff)/nbr_set))

        #plt.ylim([-1,1])
        prename = csv_mptcp_s[2*i].split("/")[-1]
        plt.savefig(os.path.join(plotfile[0], prename[:-4] + "_" + option + '.eps'))
        plt.close('all')
    
    close_files(mptcp_fd)
    
def all_plot_box_mp(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, option, plotfile):

    results = init_dict(csv_mptcp_s, nbr_set)
    
    mptcp_fd = init_files(csv_mptcp_s)
    
    summaries = init_summaries(mptcp_fd)
    
    for i in range(len(summaries)/2):
        for row1, row2 in zip(summaries[2*i],summaries[2*i+1]):
            diff = 0
            index = 0
		
            if min_diff < 0:
                diff = int(row1[val_diff_1])-int(row1[val_diff_2])
            else:
                diff = int(math.fabs(int(row1[val_diff_1])-int(row1[val_diff_2])))
            
            index = (diff-min_diff)*nbr_set/(max_diff-min_diff)
            
            compute(row1, row2, results, index, csv_mptcp_s[2*i], option)

	
    x_names = []
    x_numbers = []
    annotation = []
    vlines = []
    o = float(max_diff-min_diff)/float(nbr_set)
    data = []    
    l = 1
    for i in range(len(summaries)/2):
        for j in range(nbr_set):
            data.append(results[csv_mptcp_s[2*i]][j])
            x_numbers.append(l)
            if j == 0:
                x_names.append("[" + str(int(min_diff)) + "," + str(int(min_diff + (j+1)*o)) + "]")
            elif j == nbr_set-1:
                x_names.append("]" + str(int(min_diff + j*o)) + "," + str(max_diff) + "]")
            else:
                x_names.append("]" + str(int(min_diff + j*o)) + "," + str(int(min_diff + (j+1)*o)) + "]")
            l += 1
        data.append([])
        m = csv_mptcp_s[i*2].split("/")[-1].split("_")[-1][:-4]
        annotation.append(tuple((l-1,str(m)+"kB")))
        if i + 1 < len(summaries)/2:
            vlines.append(l)
        l += 1
        
    fig = plt.figure(figsize=(25,10))
    plt.xlabel(xlabel_name(val_diff_1[:-2]))
    plt.ylabel(ylabel_name(option))
    
    plt.boxplot(data)
    
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
    
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax+0.4,ymin,ymax+0.02])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,ymax], weight='bold', size = 'large')
    
    plt.xticks(x_numbers, x_names)
    
    plt.savefig(os.path.join(plotfile[0], option + '.eps'))
    plt.close('all')
    
    close_files(mptcp_fd)

plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'complete_r', dir_plot)
plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'request_per_time', dir_plot)
plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'total_mean', dir_plot)
plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'waiting_mean', dir_plot)
plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'connect_mean', dir_plot)
plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'process_mean', dir_plot)

all_plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'complete_r', dir_plot)
all_plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'request_per_time', dir_plot)
all_plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'total_mean', dir_plot)
all_plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'waiting_mean', dir_plot)
all_plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'connect_mean', dir_plot)
all_plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'process_mean', dir_plot)
