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

def compute(row, results, index, csv_filename, option):
    if option == 'aggreg':
        thr = float(row['seq_acked']) / float(row['con_time']) / 1000000.0 * 8.0
        
        Cmax = max(int(row['capacity_1']),int(row['capacity_2']))
        if thr >= Cmax:
            results[csv_filename][index].append((thr-Cmax)/(float(row['capacity_1'])+float(row['capacity_2'])-Cmax))
        else:
            if (thr-Cmax)/float(Cmax) < -0.75:
                print("Attention" + str((thr-Cmax)/float(Cmax)))
                print(csv_filename)
                print(option)
                print(row['capacity_1']+','+row['capacity_2']+'-'+row['delay_1']+','+row['delay_2']+'-'+row['queue_1']+','+row['queue_2'])
            results[csv_filename][index].append((thr-Cmax)/float(Cmax))
    elif option == 'retrans':
        retrans = int(int(row['bytes_transmitted_1']) + int(row['bytes_transmitted_2']))\
                    - int(row['seq_acked']) - 1428 * (int(row['reinjection_of_pkt_caused_by_1'])\
                    + int(row['reinjection_of_pkt_caused_by_2']) - 1)
        results[csv_filename][index].append(float(retrans)/float(row['seq_acked']))
    elif option == 'reinj':
        reinj = int(row['reinjection_of_pkt_caused_by_1']) + int(row['reinjection_of_pkt_caused_by_2'])
        results[csv_filename][index].append(float(reinj)*1428.0/float(row['seq_acked']))
        if float(reinj)*1428.0/float(row['seq_acked']) > 0.006:
            print("Attention" + str(float(reinj)*1428.0/float(row['seq_acked'])))
            print(csv_filename)
            print(option)
            print(row['capacity_1']+','+row['capacity_2']+'-'+row['delay_1']+','+row['delay_2']+'-'+row['queue_1']+','+row['queue_2'])
    elif option == 'first_path':
        index = 0 if int(row_tcp['seq_acked']) >= int(row['seq_acked_2']) else 1
        thr = float(row['seq_acked']) / float(row['con_time']) / 1000000.0 * 8.0
        
        Cmax = max(int(row['capacity_1']),int(row['capacity_2']))
        if thr >= Cmax:
            results[csv_filename][index].append((thr-Cmax)/(float(row['capacity_1'])+float(row['capacity_2'])-Cmax))
        else:
            results[csv_filename][index].append((thr-Cmax)/float(Cmax))
    elif option == 'percent_path':
        results[csv_filename][index].append(float(row['bytes_transmitted_1']) / (float(row['bytes_transmitted_1']) + float(row['bytes_transmitted_2'])))

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
            if (mptcp_tot_thr-tcp_max_thr)/tcp_min_thr < 0.25 and csv_filename.split("/")[-2] != 'lia_highbdp' :
            	print option + " " + csv_filename
                print "path 1 : capacity : " + row_mptcp['capacity_1'] + "Mbps, delay : " + row_mptcp['delay_1'] + ", queue : " + row_mptcp['queue_1'] + "pkts"
                print "path 2 : capacity : " + row_mptcp['capacity_2'] + "Mbps, delay : " + row_mptcp['delay_2'] + ", queue : " + row_mptcp['queue_2'] + "pkts"
                print "exp aggrg ben : " + str((mptcp_tot_thr-tcp_max_thr)/tcp_min_thr)
            results[csv_filename][index].append((mptcp_tot_thr-tcp_max_thr)/tcp_min_thr)
        else:
            if (mptcp_tot_thr-tcp_max_thr)/tcp_max_thr < 0.25 and csv_filename.split("/")[-2] != 'lia_highbdp' :
            	print option + " " + csv_filename
                print "path 1 : capacity : " + row_mptcp['capacity_1'] + "Mbps, delay : " + row_mptcp['delay_1'] + ", queue : " + row_mptcp['queue_1'] + "pkts"
                print "path 2 : capacity : " + row_mptcp['capacity_2'] + "Mbps, delay : " + row_mptcp['delay_2'] + ", queue : " + row_mptcp['queue_2'] + "pkts"
                print "exp aggrg ben : " + str((mptcp_tot_thr-tcp_max_thr)/tcp_max_thr)
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
        name = 'Ratio of bytes transmitted on the first path'
    elif val == 'capacity': 
        name = val.capitalize() + ' max. difference [Mbps]'
    elif val == 'delay':
        name = val.capitalize() + ' max. difference [ms]'
    elif val == 'queue':
        name = val.capitalize() + ' max. difference [Packets]'
    return name

def ylabel_name(option):
    name = ''
    if option == 'first_path' or option == 'aggreg':
        name = 'Theoretical Aggregation Benefit'
    elif option == 'reinj':
        name = 'Ratio of Reinjections'
    elif option == 'retrans':
        name = 'Ratio of Retransmissions' 
    elif option == 'percent_path':
        name = 'CDF'
    return name


def plot_box_mp(csv_mptcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, option, plotfile):

    results = init_dict(csv_mptcp_s, nbr_set)
    
    mptcp_fd = init_files(csv_mptcp_s)
    
    summaries = init_summaries(mptcp_fd)
    
    for i in range(len(summaries)):
        for row in summaries[i]:
            diff = 0
            index = 0
            if val_diff_1 == 'queue_delay' and option != 'first_path':
                diff = int(math.fabs(int(row['queue_1']*12.0/float(row['capacity_1']))-int(row['queue_1']*12.0/float(row['capacity_1']))))
            elif option == 'percent_path':
                diff = int(row[val_diff_1])-int(row[val_diff_2])
            elif option != 'first_path':
                diff = int(math.fabs(int(row[val_diff_1])-int(row[val_diff_2])))
            index = (diff-min_diff)*nbr_set/(max_diff-min_diff)
            
            compute(row, results, index, csv_mptcp_s[i], option)
	
    for i in range(len(summaries)):
        x_names = []
        x_numbers = []
        data = []
        p = float(max_diff-min_diff)/float(nbr_set)
        l = 1
        for j in range(nbr_set):
            data.append(results[csv_mptcp_s[i]][j])
            x_numbers.append(l)
            if j == 0:
                x_names.append("[" + str(int(min_diff)) + "," + str(int(min_diff + (j+1)*p)) + "]")
            elif j < nbr_set - 1:
                x_names.append("]" + str(int(min_diff + j*p)) + "," + str(int(min_diff + (j+1)*p)) + "]")
            else:
                x_names.append("]" + str(int(min_diff + j*p)) + "," + str(int(max_diff)) + "]")
            l += 1

        fig = plt.figure()
        plt.xlabel(xlabel_name(val_diff_1[:-2],option))
        plt.ylabel(ylabel_name(option))
        if option == 'percent_path':
            colors = ['r-','g--','b','c','m','y','k','w']
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
                title = title + ' '+ str(j) +'. '+colors[j%len(colors)]
                j = j + 1
        else:
            plt.boxplot(data)
        
        if option == 'first_path':
            plt.xticks([1,2],['Best path first','Worst path first'])
        elif option != 'percent_path':
            plt.xticks(x_numbers,x_names)
        if option == 'percent_path':
            plt.ylim([0,1])
            plt.legend(["First path has\na smaller "+val_diff_1[:-2],"First path has\na higher "+val_diff_1[:-2]], loc=4)
        elif option == 'retrans':
            plt.ylim([0,0.06])
        elif option == 'reinj':
            print("bonjour")
            plt.ylim([0,0.012])
        else:
            plt.ylim([-1,1.2])
            
        prename = csv_mptcp_s[i].split("/")[-1]
        plt.savefig(os.path.join(plotfile[0], prename[:-4] + "_" + option + 'new_4.eps'))
        plt.close('all')
    
    close_files(mptcp_fd)
    
def plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, option):
    results = init_dict(csv_mptcp_s, nbr_set)
    
    mptcp_fd = init_files(csv_mptcp_s)
    tcp_fd = init_files(csv_tcp_s)
    
    summaries_mptcp = init_summaries(mptcp_fd)
    summaries_tcp = init_summaries(tcp_fd)

    for i in range(len(summaries_mptcp)):
        for row_mptcp, row_tcp in zip(summaries_mptcp[i], summaries_tcp[i]):
            diff = 0
            if min_diff > -1: 
                diff = int(math.fabs(int(row_mptcp[val_diff_1])-int(row_mptcp[val_diff_2])))
            else :
                diff = int(int(row_mptcp[val_diff_1])-int(row_mptcp[val_diff_2])    )
            index = (diff-min_diff)*nbr_set/(max_diff-min_diff)
            
            compute_exp(row_mptcp, row_tcp, results, index, csv_mptcp_s[i], option)
    
    close_files(mptcp_fd)
    close_files(tcp_fd)
    
    return results

def per_sched_and_filesize_box(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name, nbr_sched):
    results = plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2,'aggreg')
    
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
            x_names.append(str(m) + "kB\n" + str(o))
            l += 1     
            if (i+1) % nbr_sched == 0:
                data.append([])
                l += 1
        if j == 0:
            annotation.append(tuple((float(l - 1),"[" + str(int(min_diff)) + "," + str(int(min_diff + (j+1)*p)) + "]")))
        elif j == nbr_set-1:
            annotation.append(tuple((float(l - 1),"]" + str(int(min_diff + j*p)) + "," + str(max_diff) + "]")))
        else:
            annotation.append(tuple((float(l - 1),"]" + str(int(min_diff + j*p)) + "," + str(int(min_diff + (j+1)*p)) + "]")))
        if j+1 < nbr_set:
            data.append([])
            vlines.append(float(l))
            l += 1
         

    fig = plt.figure(figsize=(25,10))
    plt.xlabel(val_diff_1[:-2].capitalize() + ' difference', size = 'x-large')
    plt.ylabel('Experimental Aggregation Benefit', size = 'x-large')
    plt.boxplot(data)
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
        
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax+0.5,ymin,ymax+0.08])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,ymax], weight='bold', size='large')
    plt.xticks(x_numbers,x_names, size='large')
    #plt.ylim([-1,1])
    #plt.show()
    plt.savefig(os.path.join(plotfile[0], name + '.eps'))
    plt.close('all')

def per_filesize_and_sched_box(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name, nbr_sched):
    results = plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2,'aggreg')

    x_numbers = []
    x_names = []
    data = []
    l = 1
    o = float(max_diff-min_diff)/float(nbr_set)
    vlines = []
    annotation = []
    for i in range(len(csv_mptcp_s)/nbr_sched):
        for j in range(nbr_set):
            for k in range(nbr_sched):
                m = csv_mptcp_s[nbr_sched*i+k]
                data.append(results[m][j])
                x_numbers.append(l)
                n = m.split("/")[-1][8:-4] 
                if j == 0:
                    x_names.append("[" + str(int(min_diff)) + "," + str(int(min_diff + (j+1)*o)) + "]")
                elif j == nbr_set-1:
                    x_names.append("]" + str(int(min_diff + j*o)) + "," + str(max_diff) + "]")
                else:
                    x_names.append("]" + str(int(min_diff + j*o)) + "," + str(int(min_diff + (j+1)*o)) + "]")
                   
                l += 1
        m = csv_mptcp_s[nbr_sched*i].split("/")[-1][8:-4]
        annotation.append(tuple((float(l - 1),str(m)+"kB")))
        if i+1 < len(csv_mptcp_s)/nbr_sched:
            data.append([])
            vlines.append(float(l))
            l += 1
        

    fig = plt.figure(figsize=(25,10))
    plt.xlabel(val_diff_1[:-2].capitalize() + ' difference', size = 'x-large')
    plt.ylabel('Experimental Aggregation Benefit', size = 'x-large')
    plt.boxplot(data)
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
    
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax+0.5,ymin,ymax+0.08])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,ymax], weight='bold', size='large')
    plt.xticks(x_numbers,x_names, fontsize='large')
    #plt.ylim([-1,1])
    #plt.show()
    plt.savefig(os.path.join(plotfile[0], name + '.eps'))
    plt.close('all')
    
def exp_aggr_ben(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name):
    results = plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2,'aggreg')

    for i in range(len(csv_mptcp_s)):
        x_numbers = []
        x_names = []
        data = []
        l = 1
        o = float(max_diff-min_diff)/float(nbr_set)
        for j in range(nbr_set):
            data.append(results[csv_mptcp_s[i]][j])
            x_numbers.append(l)            
            if j == 0:
                x_names.append("[" + str(int(min_diff)) + "," + str(int(min_diff + (j+1)*o)) + "]")
            elif j == nbr_set-1:
                x_names.append("]" + str(int(min_diff + j*o)) + "," + str(max_diff) + "]")
            else:
                x_names.append("]" + str(int(min_diff + j*o)) + "," + str(int(min_diff + (j+1)*o)) + "]")
            l += 1


        fig = plt.figure()
        plt.xlabel(val_diff_1[:-2].capitalize() + ' difference')
        plt.ylabel('Experimental Aggregation Benefit')
        plt.boxplot(data)
        plt.xticks(x_numbers,x_names)
        plt.ylim([-1,1.5])
        prename = csv_mptcp_s[i].split("/")[-1]
        plt.savefig(os.path.join(plotfile[0], prename[:-4] + "_" + name + '_new2.eps'))
        plt.close('all')

def exp_first_path(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name):
    results = plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, name)

    for i in range(len(csv_mptcp_s)):
        data = []
        for j in range(nbr_set):
            data.append(results[csv_mptcp_s[i]][j])
            
            

        fig = plt.figure()
        plt.xlabel('First Path used')
        plt.ylabel('Experimental Aggregation Benefit')
        plt.boxplot(data)
        plt.xticks(range(1,nbr_set+1),['Best first', 'Worst first'])
        plt.ylim([-1,1.5])
        prename = csv_mptcp_s[i].split("/")[-1]
        plt.savefig(os.path.join(plotfile[0], prename[:-4] + "_" + name + '_exp_new.eps'))
        plt.close('all')
        
def exp_first_path_per_size_per_sched(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, plotfile, name, nbr_sched):
    results = plot_box_mp_experimental(csv_mptcp_s, csv_tcp_s, min_diff, max_diff, nbr_set, val_diff_1, val_diff_2, 'first_path')
    
    x_numbers = []
    x_names = []
    data = []
    l = 0
    vlines = []
    annotation = []
    for i in range(len(csv_mptcp_s)/nbr_sched):
        m = csv_mptcp_s[i*nbr_sched].split("/")[-1][8:-4]
        n = 0
        for j in range(nbr_set):
            for k in range(nbr_sched):
                data.append(results[csv_mptcp_s[i*nbr_sched+k]][j])
                n += 1
            if nbr_sched > 2:
                data.append([])
                n += 1
       	x_numbers.append(float(l + float((nbr_sched*nbr_set+1.0)/4.0+0.25)))
       	x_numbers.append(float(l + float(3*(nbr_sched*nbr_set+1.0)/4.0-0.25)))
       	x_names.append("Best first")
       	x_names.append("Worst first")
       	annotation.append(tuple((float(l + n),str(m)+"kB")))
       	if i+1 < (len(csv_mptcp_s)/nbr_sched):
            data.append([])
            n += 1
            vlines.append(float(l + nbr_sched*nbr_set + 1))
            l += n

    fig = plt.figure(figsize=(25,10))
    plt.xlabel('First Path used', size = 'x-large')
    plt.ylabel('Experimental Aggregation Benefit', size = 'x-large')
    plt.boxplot(data)
    for i in vlines:
        plt.axvline(x=i,ls='dashed',color='k')
    
    [xmin,xmax,ymin,ymax] = plt.axis()
    plt.axis([xmin,xmax+0.5,ymin,ymax+0.08])
    for (x,text) in annotation:
        plt.annotate(s=text,xy=[x,ymax], weight='bold', size = 'large')
    
    plt.xticks(x_numbers  , x_names, size = 'large')
    #plt.ylim([-1,1])
    plt.savefig(os.path.join(plotfile[0], name + '.eps'))
    plt.close('all')

 
def histo_param(csv_mptcp):
    with open(csv_mptcp, 'rb') as csvmptcp:
        print 'hello'
	#plt.hist()

#plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'aggreg', dir_plot)
#experimental_aggr_benef_box_mp(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'exp_aggr_ben')
#per_sched_and_filesize_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_sched_and_filesize', int(args.nbr_sched))
#per_filesize_and_sched_box(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'per_filesize_and_sched', int(args.nbr_sched))
#exp_aggr_ben(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, dir_plot, 'exp_aggr_ben')
#exp_first_path(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), 2, args.val_first, args.val_second, dir_plot, 'first_path_theory')
#exp_first_path(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), 2, args.val_first, args.val_second, dir_plot, 'first_path')
#exp_first_path_per_size_per_sched(args.mptcp.split(","), args.tcp.split(","), int(args.min), int(args.max), 2, args.val_first, args.val_second, dir_plot, 'all_first_path', int(args.nbr_sched))
#plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'retrans', dir_plot)
plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'reinj', dir_plot)
#plot_box_mp(args.mptcp.split(","), int(args.min), int(args.max), 2, args.val_first, args.val_second, 'first_path', dir_plot)
#plot_box_mp(args.mptcp.split(","), -int(args.max), int(args.max), int(args.nbr_set), args.val_first, args.val_second, 'percent_path', dir_plot)
