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
parser.add_argument("-a",
		"--app", help="application used for experiments")
parser.add_argument("-m",
		"--mptcp", help="CSV file containing MPTCP stats summary")
parser.add_argument("-t",
		"--tcp", help="CSV file containing TCP stats summary")
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
parser.add_argument("-b",
		"--nbr-sched", help="Number of scheduler tested with mptcp")

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

def compute(row, results, index, csv_filename, option, row_tcp=None):
    if option == 'aggreg':
        thr = float(row['seq_acked']) / float(row['con_time']) / 1000000.0 * 8.0
        
        Cmax = max(int(row['capacity_1']),int(row['capacity_2']))
        if thr >= Cmax:
            results[csv_filename][index].append((thr-Cmax)/(float(row['capacity_1'])+float(row['capacity_2'])-Cmax))
        else:
            results[csv_filename][index].append((thr-Cmax)/float(Cmax))
    elif option == 'retrans':
        retrans = int(int(row['bytes_transmitted_1']) + int(row['bytes_transmitted_2']))\
                    - int(row['seq_acked']) - 1428 * (int(row['reinjection_of_pkt_caused_by_1'])\
                    + int(row['reinjection_of_pkt_caused_by_2']) - 1)
        results[csv_filename][index].append(float(retrans)/float(row['seq_acked']))
    elif option == 'reinj':
        reinj = int(row['reinjection_of_pkt_caused_by_1']) + int(row['reinjection_of_pkt_caused_by_2'])
        results[csv_filename][index].append(float(reinj)*1428.0/float(row['seq_acked']))
    elif option == 'first_path':
        index = 0 if int(row['bytes_transmitted_1']) >= int(row['bytes_transmitted_2']) else 1
        thr = float(row['seq_acked']) / float(row['con_time']) / 1000000.0 * 8.0
        
        Cmax = max(int(row['capacity_1']),int(row['capacity_2']))
        if thr >= Cmax:
            results[csv_filename][index].append((thr-Cmax)/(float(row['capacity_1'])+float(row['capacity_2'])-Cmax))
        else:
            results[csv_filename][index].append((thr-Cmax)/float(Cmax))
    elif option == 'percent_path':
    	retrans_1 = float(row_tcp['seq_acked']) / float(row_tcp['bytes_transmitted_1'])
        
        retrans_2 = float(row_tcp['seq_acked_2']) / float(row_tcp['bytes_transmitted_2'])
                    
        if float(retrans_1) >= float(retrans_2):
            results[csv_filename][0].append(float(row['bytes_transmitted_1']) / (float(row['bytes_transmitted_1']) + float(row['bytes_transmitted_2'])))
        else:
            results[csv_filename][0].append(float(row['bytes_transmitted_2']) / (float(row['bytes_transmitted_1']) + float(row['bytes_transmitted_2'])))


def compute_exp(row_mptcp, row_tcp, results, index, csv_filename, option):
    if option == 'aggreg':
        mptcp_tot_thr = float(row_mptcp['seq_acked']) / float(row_mptcp['con_time']) / 1000000.0 * 8.0
        
        tcp_thr_1 = float(row_tcp['seq_acked']) / float(row_tcp['con_time']) / 1000000.0 * 8.0
        tcp_thr_2 = float(row_tcp['seq_acked_2']) / float(row_tcp['con_time_2']) / 1000000.0 * 8.0
                
        tcp_max_thr = max(tcp_thr_1, tcp_thr_2)
        tcp_min_thr = min(tcp_thr_1, tcp_thr_2)
        tcp_tot_thr = tcp_thr_1 + tcp_thr_2
        if mptcp_tot_thr >= tcp_tot_thr:
            if mptcp_tot_thr/tcp_tot_thr > 100 :
            	print option + " " + csv_filename
                print "path 1 : capacity : " + row_mptcp['capacity_1'] + "Mbps, delay : " + row_mptcp['delay_1'] + ", queue : " + row_mptcp['queue_1'] + "pkts"
                print "path 2 : capacity : " + row_mptcp['capacity_2'] + "Mbps, delay : " + row_mptcp['delay_2'] + ", queue : " + row_mptcp['queue_2'] + "pkts"
                print "exp aggrg ben : " + str(mptcp_tot_thr/tcp_tot_thr)
            results[csv_filename][index].append(mptcp_tot_thr/tcp_tot_thr)
        elif mptcp_tot_thr >= tcp_max_thr:
            results[csv_filename][index].append((mptcp_tot_thr-tcp_max_thr)/tcp_min_thr)
        else:
            results[csv_filename][index].append((mptcp_tot_thr-tcp_max_thr)/tcp_max_thr)
    elif option == 'first_path':
        index = 0 if int(row_tcp['seq_acked']) >= int(row_tcp['seq_acked_2']) else 1
        mptcp_tot_thr = float(row_mptcp['seq_acked']) / float(row_mptcp['con_time']) / 1000000.0 * 8.0
        
        tcp_thr_1 = float(row_tcp['seq_acked']) / float(row_tcp['con_time']) / 1000000.0 * 8.0
        tcp_thr_2 = float(row_tcp['seq_acked_2']) / float(row_tcp['con_time_2']) / 1000000.0 * 8.0
                
        tcp_max_thr = max(tcp_thr_1, tcp_thr_2)
        tcp_min_thr = min(tcp_thr_1, tcp_thr_2)
        tcp_tot_thr = tcp_thr_1 + tcp_thr_2
        if mptcp_tot_thr >= tcp_tot_thr:
            results[csv_filename][index].append(mptcp_tot_thr/tcp_tot_thr)
        elif mptcp_tot_thr >= tcp_max_thr:
            results[csv_filename][index].append((mptcp_tot_thr-tcp_max_thr)/tcp_min_thr)
        else:
            results[csv_filename][index].append((mptcp_tot_thr-tcp_max_thr)/tcp_max_thr)
    elif option == 'first_path_theory':
        index = 0 if int(row_tcp['seq_acked']) >= int(row_tcp['seq_acked_2']) else 1
        thr = float(row_mptcp['seq_acked']) / float(row_mptcp['con_time']) / 1000000.0 * 8.0
        
        Cmax = max(int(row_tcp['capacity_1']),int(row_tcp['capacity_2']))
        if thr >= Cmax:
            results[csv_filename][index].append((thr-Cmax)/(float(row_tcp['capacity_1'])+float(row_tcp['capacity_2'])-Cmax))
        else:
            results[csv_filename][index].append((thr-Cmax)/float(Cmax))
    	

def xlabel_name(val,option):
    name = val.capitalize() + 'max difference'
    if option == 'percent_path':
        name = 'Ratio of bytes transmitted on the less lossy path'
    elif val == 'capacity': 
        name = val.capitalize() + ' difference [Mbps]'
    elif val == 'delay':
        name = val.capitalize() + ' difference [ms]'
    elif val == 'queue':
        name = val.capitalize() + ' difference [Packets]'
    elif val == 'losses':
    	if option == 'mean':
    		name = 'Packet-loss unweighted mean probability [%]'
    	elif option == 'max':
    		name = 'Maximal Packet-loss probability over both path [%]'
    	elif option == 'min':
    		name = 'Minimal Packet-loss probability over both path [%]'
    	elif option == 'one':
    		name = 'Packet-loss probability on first path [%]'
    	elif option == 'two':
    		name = 'Packet-loss probability on second path [%]'
    	else:
    		name = 'Packet-loss weighted mean probability [%]'
    return name

def ylabel_name(option):
    name = ''
    if option == 'first_path' or option == 'aggreg':
        name = 'Aggregation Benefit'
    elif option == 'reinj':
        name = 'Ratio of Reinjections'
    elif option == 'retrans':
        name = 'Ratio of Retransmissions' 
    elif option == 'percent_path':
        name = 'CDF'
    return name

def plot_box_mp(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, option, plotfile, csv_tcp_s=None):

    results = init_dict(csv_mptcp_s, nbr_set)
    
    mptcp_fd = init_files(csv_mptcp_s)
    tcp_fd = init_files(csv_tcp_s)
    
    summaries = init_summaries(mptcp_fd)
    summaries_tcp = init_summaries(tcp_fd)
    
    for i in range(len(summaries)):
        for row, row_tcp in zip(summaries[i],summaries_tcp[i]):
            diff = 0
            index = 0
            diff = int(float(row[val_diff_1]))-int(float(row[val_diff_2]))
            
            index = (diff-min_diff)*nbr_set/(max_diff-min_diff)
            
            compute(row, results, index, csv_mptcp_s[i], option, row_tcp)
	
	data = []
    for i in range(len(summaries)):
        data.append(results[csv_mptcp_s[i]][0])
        
    fig = plt.figure()
    plt.xlabel(xlabel_name(val_diff_1[:-2],option))
    plt.ylabel(ylabel_name(option))
    if option == 'percent_path':
        colors = ['r-+','g-^','b-d','k-o']
        j = 0
        title = 'Color order : '
        for dset in data:
            x = []
            x.append(0)
            for x_elem in sorted(dset):
                x.append(x_elem)
            x.append(1)
            y = [1.0/float(len(dset))]*len(dset)
            z = []
            z.append(0)
            for z_elem in np.cumsum(y): 
                z.append(z_elem)
            z.append(1)
            plt.plot(x, z, colors[j%len(colors)])
            j = j + 1
    
    if option == 'percent_path':
        plt.ylim([0,1])
        plt.legend(["LIA","OLIA","BaLIA","wVegas"], loc=2)
        
    prename = csv_mptcp_s[i].split("/")[-1]
    plt.savefig(os.path.join(plotfile[0], prename[:-4] + "_" + option + 'new_6.eps'))
    plt.close('all')
    
    close_files(mptcp_fd)


def collect_box_mp(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, option, sub):
    results = init_dict(csv_mptcp_s, nbr_set)
    
    mptcp_fd = init_files(csv_mptcp_s)
    
    summaries = init_summaries(mptcp_fd)
    
    for i in range(len(summaries)):
        for row in summaries[i]:
            diff = 0
            index = 0
            if val_diff_1[:-2] == 'losses':
            	if sub == 'max':
                	diff = max(float(row[val_diff_1]),float(row[val_diff_2]))
                	diff = min(max_diff-0.05,diff)
                elif sub == 'min':
                	diff = min(float(row[val_diff_1]),float(row[val_diff_2]))
                elif sub == 'one':
                	diff = float(row[val_diff_1])
                	diff = min(max_diff-0.05,diff)
                elif sub == 'two':
                	diff = float(row[val_diff_2])
                	diff = min(max_diff-0.05,diff)
                elif sub == 'mean':
                	diff = (float(row[val_diff_1])+float(row[val_diff_2]))/2.0
                	diff = min(max_diff-0.05,diff)
                else:
                	thr1 = float(row['bytes_transmitted_1'])
                	thr2 = float(row['bytes_transmitted_2'])
                	sum_thr = thr1+thr2
                	diff = (int(float(row[val_diff_1]))*thr1+int(float(row[val_diff_2]))*thr2)/float(sum_thr)
                	diff = min(max_diff-0.05,diff)
            else :
                if min_diff > -1: 
                    diff = int(math.fabs(int(row[val_diff_1])-int(row[val_diff_2])))
                else :
                    diff = int(int(row[val_diff_1])-int(row[val_diff_2]))
            index = int((diff-min_diff)*nbr_set/(max_diff-min_diff))
            
            compute(row, results, index, csv_mptcp_s[i], option)
    
    close_files(mptcp_fd)
    
    return results

def per_sched_and_filesize_box_theory(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name, nbr_sched, sub = ''):
    results = collect_box_mp(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2,'aggreg', sub)
    
    x_numbers = []
    x_names = []
    data = []
    l = 1
    vlines = []
    annotation = []
    p = float(max_diff-min_diff)/float(nbr_set)
    for j in range(nbr_set):
        for i in range(len(csv_mptcp_s)):
            data.append(results[csv_mptcp_s[i]][j])
            m = csv_mptcp_s[i].split("/")[-1][8:-4]
            o = csv_mptcp_s[i].split("/")[-2].split("_")[0]
            x_numbers.append(l)
            x_names.append(str(o))
            l += 1     
            if (i+1) % nbr_sched == 0  and j + 1 < nbr_set:
                #data.append([])
            	vlines.append(float(l-0.5))
        if j == 0:
            annotation.append(tuple((float(l - 2.1),"[" + str("%.2f" % min_diff) + "," + str("%.2f" % (min_diff + (j+1)*p)) + "]")))
        elif j == nbr_set-1:
            annotation.append(tuple((float(l - 2.1),"]" + str("%.2f" % (min_diff + j*p)) + "," + str("%.2f" % max_diff) + "]")))
        else:
            annotation.append(tuple((float(l - 2.1),"]" + str("%.2f" % (min_diff + j*p)) + "," + str("%.2f" % (min_diff + (j+1)*p)) + "]"))) 

    fig = plt.figure(figsize=(25,10))
    plt.xlabel(xlabel_name(val_diff_1[:-2],sub), size = 'xx-large')
    plt.ylabel('Theoretical Aggregation Benefit', size = 'xx-large')
    plt.boxplot(data)
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
        
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax,-1,1.6])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,1.52], weight='bold', size='xx-large')
    plt.xticks(x_numbers,x_names, size='xx-large')
    #plt.ylim([-1,1])
    #plt.show()
    plt.savefig(os.path.join(plotfile[0], name + sub + '___theory_final_8.eps'))
    plt.close('all')
    
def plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, option, sub):
    results = init_dict(csv_mptcp_s, nbr_set)
    
    mptcp_fd = init_files(csv_mptcp_s)
    tcp_fd = init_files(csv_tcp_s)
    
    summaries_mptcp = init_summaries(mptcp_fd)
    summaries_tcp = init_summaries(tcp_fd)

    for i in range(len(summaries_mptcp)):
        for row_mptcp, row_tcp in zip(summaries_mptcp[i], summaries_tcp[i]):
            diff = 0
            if val_diff_1[:-2] == 'losses':
            	if sub == 'max':
                	diff = max(float(row_mptcp[val_diff_1]),float(row_mptcp[val_diff_2]))
                	diff = min(max_diff-0.05,diff)
                elif sub == 'min':
                	diff = min(float(row_mptcp[val_diff_1]),float(row_mptcp[val_diff_2]))
                elif sub == 'one':
                	diff = float(row_mptcp[val_diff_1])
                	diff = min(max_diff-0.05,diff)
                elif sub == 'two':
                	diff = float(row_mptcp[val_diff_2])
                	diff = min(max_diff-0.05,diff)
                elif sub == 'mean':
                	diff = (float(row_mptcp[val_diff_1])+float(row_mptcp[val_diff_2]))/2.0
                	diff = min(max_diff-0.05,diff)
                else:
                	thr1 = float(row_mptcp['bytes_transmitted_1'])
                	thr2 = float(row_mptcp['bytes_transmitted_2'])
                	sum_thr = thr1+thr2
                	diff = (int(float(row_mptcp[val_diff_1]))*thr1+int(float(row_mptcp[val_diff_2]))*thr2)/float(sum_thr)
                	diff = min(max_diff-0.05,diff)
            else :
                if min_diff > -1: 
                    diff = int(math.fabs(int(row_mptcp[val_diff_1])-int(row_mptcp[val_diff_2])))
                else :
                    diff = int(int(row_mptcp[val_diff_1])-int(row_mptcp[val_diff_2]))
            index = int((diff-min_diff)*nbr_set/(max_diff-min_diff))
            
            compute_exp(row_mptcp, row_tcp, results, index, csv_mptcp_s[i], option)
    
    close_files(mptcp_fd)
    close_files(tcp_fd)
    
    return results

def per_sched_and_filesize_box(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name, nbr_sched, sub=''):
    results = plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2,'aggreg', sub)
    
    x_numbers = []
    x_names = []
    data = []
    l = 1
    vlines = []
    annotation = []
    p = float(max_diff-min_diff)/float(nbr_set)
    for j in range(nbr_set):
        for i in range(len(csv_mptcp_s)):
            data.append(results[csv_mptcp_s[i]][j])
            m = csv_mptcp_s[i].split("/")[-1][8:-4]
            o = csv_mptcp_s[i].split("/")[-2].split("_")[0]
            x_numbers.append(l)
            x_names.append(str(o))
            l += 1     
            if (i+1) % nbr_sched == 0 and j + 1 < nbr_set :
                #data.append([])
            	vlines.append(float(l-0.5))
                #l += 1
        if j == 0:
            annotation.append(tuple((float(l - 2.1),"[" + str("%.2f" % min_diff) + "," + str("%.2f" % (min_diff + (j+1)*p)) + "]")))
        elif j == nbr_set-1:
            annotation.append(tuple((float(l - 2.1),"]" + str("%.2f" % (min_diff + j*p)) + "," + str("%.2f" % max_diff) + "]")))
        else:
            annotation.append(tuple((float(l - 2.1),"]" + str("%.2f" % (min_diff + j*p)) + "," + str("%.2f" % (min_diff + (j+1)*p)) + "]"))) 

    fig = plt.figure(figsize=(25,10))
    plt.xlabel(xlabel_name(val_diff_1[:-2],'aggreg'), size = 'xx-large')
    plt.ylabel('Experimental Aggregation Benefit', size = 'xx-large')
    plt.boxplot(data)
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
        
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax,-1, 1.6])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,1.52], weight='bold', size='xx-large')
    plt.xticks(x_numbers,x_names, size='xx-large')
    #plt.ylim([-1,1])
    #plt.show()
    plt.savefig(os.path.join(plotfile[0], name + sub + '___exp_final_2.eps'))
    plt.close('all')
        
def exp_first_path_per_size_per_sched(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name, nbr_sched, sub =''):
    results = plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, name, sub)
    
    x_numbers = []
    x_names = []
    data = []
    l = 1
    vlines = []
    annotation = []
    for i in range(len(csv_mptcp_s)/nbr_sched):
        for j in range(nbr_set):
            for k in range(nbr_sched):
                data.append(results[csv_mptcp_s[i*nbr_sched+k]][j])
                o = csv_mptcp_s[i*nbr_sched+k].split("/")[-2].split("_")[0]
                x_numbers.append(l)
                x_names.append(str(o))
                l += 1
            if j < nbr_set - 1:
                annotation.append(tuple((l - (nbr_sched)/2 - 1, "Best first")))
                if nbr_sched > 2:
                    data.append([])
                    l += 1
            else:
       	        annotation.append(tuple((l - (nbr_sched)/2 - 1, "Worst first")))

    fig = plt.figure(figsize=(15,10))
    plt.xlabel('First Path used', size = 'xx-large')
    plt.ylabel('Experimental Aggregation Benefit', size = 'xx-large')
    plt.boxplot(data)
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
    
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax,-1,1.6])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,1.52], weight='bold', size = 'xx-large')
    
    plt.xticks(x_numbers  , x_names, size = 'xx-large')
    
    plt.savefig(os.path.join(plotfile[0], name + '_exp_final_8.eps'))
    plt.close('all')

def first_path_per_size_per_sched(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name, nbr_sched, sub = ''):
    results = collect_box_mp(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, 'first_path', sub)
    
    x_numbers = []
    x_names = []
    data = []
    l = 1
    vlines = []
    annotation = []
    for i in range(len(csv_mptcp_s)/nbr_sched):
        for j in range(nbr_set):
            for k in range(nbr_sched):
                data.append(results[csv_mptcp_s[i*nbr_sched+k]][j])
                o = csv_mptcp_s[i*nbr_sched+k].split("/")[-2].split("_")[0]
                x_numbers.append(l)
                x_names.append(str(o))
                l += 1
            if j < nbr_set - 1:
                annotation.append(tuple((l - (nbr_sched)/2 - 1, "Best first")))
                if nbr_sched > 2:
                    data.append([])
                    l += 1
            else:
       	        annotation.append(tuple((l - (nbr_sched)/2 - 1, "Worst first")))

    fig = plt.figure(figsize=(15,10))
    plt.xlabel('First Path used', size = 'xx-large')
    plt.ylabel('Theoretical Aggregation Benefit', size = 'xx-large')
    plt.boxplot(data)
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
    
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax,ymin,ymin + 1.05*(ymax-ymin)])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,ymax], weight='bold', size = 'xx-large')
    
    plt.xticks(x_numbers  , x_names, size = 'xx-large')
    #plt.ylim([-1,1])
    plt.savefig(os.path.join(plotfile[0], name + '_theory_final_5.eps'))
    plt.close('all')


def histo_param(csv_mptcp):
    with open(csv_mptcp, 'rb') as csvmptcp:
        print 'hello'
	#plt.hist()

#plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'aggreg', dir_plot)
#experimental_aggr_benef_box_mp(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'exp_aggr_ben')
#per_sched_and_filesize_box_theory(args.mptcp.split(","), int(args.min), 2.5, int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize_theory', int(args.nbr_sched),'max')
#per_sched_and_filesize_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), 2.5, int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize', int(args.nbr_sched),'max')
#per_sched_and_filesize_box_theory(args.mptcp.split(","), int(args.min), 2.5, int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize_theory', int(args.nbr_sched),'one')
#per_sched_and_filesize_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), 2.5, int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize', int(args.nbr_sched),'one')
#per_sched_and_filesize_box_theory(args.mptcp.split(","), int(args.min), 2.5, int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize_theory', int(args.nbr_sched),'two')
#per_sched_and_filesize_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), 2.5, int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize', int(args.nbr_sched),'two')#
per_sched_and_filesize_box_theory(args.mptcp.split(","), int(args.min), float(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize_theory', int(args.nbr_sched))
per_sched_and_filesize_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), float(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize', int(args.nbr_sched))
#per_sched_and_filesize_box_theory(args.mptcp.split(","), int(args.min), float(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize_theory', int(args.nbr_sched),'mean')
#per_sched_and_filesize_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), float(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize', int(args.nbr_sched),'mean')
#per_sched_and_filesize_box_theory(args.mptcp.split(","), int(args.min), float(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize_theory', int(args.nbr_sched),'min')
#per_sched_and_filesize_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), float(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize', int(args.nbr_sched),'min')
#per_filesize_and_sched_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_filesize_and_sched', int(args.nbr_sched))
#exp_aggr_ben(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'exp_aggr_ben')
#exp_first_path(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), 2, args.val_first, args.val_second, dir_plot, 'first_path')
#exp_first_path_per_size_per_sched(args.mptcp.split(","), args.tcp.split(","), -80000, 80000, 2, args.val_first, args.val_second, dir_plot, 'first_path', int(args.nbr_sched))
#exp_first_path_per_size_per_sched(args.mptcp.split(","), args.tcp.split(","), -80000, 80000, 2, args.val_first, args.val_second, dir_plot, 'first_path_theory', int(args.nbr_sched))
#plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'retrans', dir_plot)
#plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'reinj', dir_plot)
#plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), 2, args.val_first, args.val_second, 'first_path', dir_plot)
#plot_box_mp(args.mptcp.split(","), -int(args.max), int(args.max), 2, args.val_first, args.val_second, 'percent_path', dir_plot, args.tcp.split(","))
