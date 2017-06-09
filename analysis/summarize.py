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
parser.add_argument("-a",
                    "--app", help="application used for experiments")
parser.add_argument("-S",
                    "--sender", help="sender : client or server ?")
parser.add_argument("-t",
                    "--topos", help="topologies used for the TCP (only) experiment")

args = parser.parse_args()

direct = os.path.abspath(os.path.expanduser(args.directory))
direct = os.path.join(direct,'graphs' + str(args.sender) + '.pcap.gz')

def template_csv(csv_file):
    csv_file_writer = csv.writer(csv_file,delimiter=',',
                           quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_file_writer.writerow(['filesize', 'con_time', 'seq_acked', \
                            'pkt_injected_once', 'capacity_1','delay_1', \
                            'queue_1', 'bytes_transmitted_1', \
                            'reinjection_of_pkt_caused_by_1', 'capacity_2', \
                            'delay_2','queue_2', \
                            'bytes_transmitted_2', 'reinjection_of_pkt_caused_by_2',\
                             'con_time_2', 'seq_acked_2', \
                            'pkt_injected_once_2'])
    return csv_file_writer

def aggregate_stats(csv_file, directory, sender, app, min_depth=0 , max_depth=0, topos=None):
    """ Enter subdirectory and analyze stats files """
    transfer_size = '0'
    if os.path.isdir(directory):
        i = 0
        for dirpath, dirnames, filename in os.walk(directory):                
            if i >= min_depth and i <= max_depth:
                for dirname in dirnames:
                    if app == 'curl':
                        s = dirname.split('_')
                        transfer_size = s[-1]
                    if topos is not None:
                        analyze_tcp_stats(csv_file, transfer_size, os.path.join(dirpath, dirname), sender, topos, 0 if app == 'curl' else 1)
                    else:
                        analyze_stats(csv_file, transfer_size, os.path.join(dirpath, dirname), sender, 0 if app == 'curl' else 1)
                i = i + 1
            else:
                if i > max_depth:
                    break
                else:
                    i = i + 1

def analyze_stats(csv_file, transfer_size, directory, sender, con_id):
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
                    name = os.path.join(name, 'tsg_thgpt')
                    to_write = [0]*15
                    to_write[0] = transfer_size
                    to_write[4:6] = topo_1
                    to_write[9:11] = topo_2
                    filename_start = sender + '_' +('s' if sender[0] == 's' else 'c') \
                                     + '2' + ('c' if sender[0] == 's' else 's')
                    
                    with open(os.path.join(name,filename_start+'_sf_'+str(con_id)+'.csv'),'rb') as analyzed_csv:
                        reader = csv.reader(analyzed_csv, delimiter=',')
                        j = 0
                        for row in reader:
                            if j == 0:
                                to_write[7] = row[1+(1-con_id)] #bytes transmitted per sf 1
                            elif j == 1:
                                to_write[12] = row[1+(1-con_id)] #bytes transmitted per sf 2
                            j = j + 1

                    with open(os.path.join(name,sender+'_stats_'+str(con_id)+'.csv'),'rb') as analyzed_csv:
                        reader = csv.reader(analyzed_csv, delimiter=';')
                        j = 0
                        for row in reader:
                            if j == 2:
                                to_write[1] = row[3+(1-con_id)] # connection time
                            elif j == 3:
                                to_write[2] = row[3+(1-con_id)] # Nbr of seq acked
                            elif j == 7:
                                to_write[3] = row[3+(1-con_id)] #injected once
                            elif j == 72:
                                to_write[8] = row[3+(1-con_id)] #reinjected caused by 1
                            elif j == 70:
                                to_write[13] = row[3+(1-con_id)] #reinjected caused by 2
                            j = j + 1
                    csv_file.writerow(to_write)

def analyze_tcp_stats(csv_file, transfer_size, directory, sender, topos, con_id):
    """ Analyze stats file and write in csv """
    if os.path.isdir(directory):
        for dirpath, dirnames, filename in os.walk(directory):                
            for dirname in dirnames:
                if dirname in topos.keys():
                    topo_1 = dirname.split('_')
                    topo_2 = topos[dirname].split('_')
                    
                    name1 = os.path.join(directory, dirname)
                    name1 = os.path.join(name1, 'tsg_thgpt')
                    
                    name2 = os.path.join(directory, topos[dirname])
                    name2 = os.path.join(name2, "tsg_thgpt")

                    to_write = [0]*17
                    to_write[0] = transfer_size
                    to_write[4:7] = topo_1
                    to_write[9:12] = topo_2
                    filename_start = sender + '_' +('s' if sender[0] == 's' else 'c') \
                                     + '2' + ('c' if sender[0] == 's' else 's')
                    
                    with open(os.path.join(name1,filename_start+'_sf_'+str(con_id)+'.csv'),'rb') as analyzed_csv:
                        reader = csv.reader(analyzed_csv, delimiter=',')
                        j = 0
                        for row in reader:
                            if j == 0:
                                to_write[7] = row[1+(1-con_id)] #bytes transmitted per sf 1
                            j = j + 1
                    
                    with open(os.path.join(name2,filename_start+'_sf_'+str(con_id)+'.csv'),'rb') as analyzed_csv:
                        reader = csv.reader(analyzed_csv, delimiter=',')
                        j = 0
                        for row in reader:
                            if j == 0:
                                to_write[12] = row[1+(1-con_id)] #bytes transmitted per sf 1
                            j = j + 1

                    with open(os.path.join(name1,sender+'_stats_'+str(con_id)+'.csv'),'rb') as analyzed_csv:
                        reader = csv.reader(analyzed_csv, delimiter=';')
                        j = 0
                        for row in reader:
                            if j == 2:
                                to_write[1] = row[3+(1-con_id)] # connection time
                            elif j == 3:
                                to_write[2] = row[3+(1-con_id)] # Nbr of seq acked
                            elif j == 7:
                                to_write[3] = row[3+(1-con_id)] #injected once
                            elif j == 72:
                                to_write[8] = row[3+(1-con_id)] #reinjected caused by 1
                            j = j + 1
                    
                    with open(os.path.join(name2,sender+'_stats_'+str(con_id)+'.csv'),'rb') as analyzed_csv:
                        reader = csv.reader(analyzed_csv, delimiter=';')
                        j = 0
                        for row in reader:
                            if j == 2:
                                to_write[14] = row[3+(1-con_id)] # connection time
                            elif j == 3:
                                to_write[15] = row[3+(1-con_id)] # Nbr of seq acked
                            elif j == 7:
                                to_write[16] = row[3+(1-con_id)] #injected once
                            elif j == 72:
                                to_write[13] = row[3+(1-con_id)] #reinjected caused by 1
                            j = j + 1
                    
                    csv_file.writerow(to_write)



def preprocess_exp_topo(csv_topos):
    all_topos = dict()
    with open(csv_topos, 'rb') as topos:
        topos_reader = csv.DictReader(topos)
        
        for row in topos_reader:
            all_topos[str(row['Capacity1'])+'_'+str(row['Delay1'])+'_'+str(row['Queuing1'])] \
                = str(row['Capacity2'])+'_'+str(row['Delay2'])+'_'+str(row['Queuing2'])

    return all_topos

csv_filename = args.csv_file
sender = args.sender

csvfile = open(csv_filename, 'w')
csv_file_writer = template_csv(csvfile)
if args.topos:
    topos = preprocess_exp_topo(args.topos)
    aggregate_stats(csv_file_writer, direct, sender, args.app, 0, 0 if args.app == "iperf" else int(args.subdirectory)-1, topos)
else:
    if args.app == "iperf":
        aggregate_stats(csv_file_writer, direct, sender, args.app, 0, 0) 
    else:
        aggregate_stats(csv_file_writer, direct, sender, args.app, 0, int(args.subdirectory)-1)

csvfile.close()
