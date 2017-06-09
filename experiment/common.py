

################################
#           IMPORTS            #
################################

import os
import os.path

HTTP_FILE = 'http_file'
HTTP_FILESIZE = 'http_file_size'
AB_TIMELIMIT = 'abTimelimit'
CURLTIMEOUT = 'curltimeout'
IPERFTIME = 'iperfTime'

CAPA_1 = 'Capacity1'
CAPA_2 = 'Capacity2'
DELAY_1 = 'Delay1'
DELAY_2 = 'Delay2'
QUEUE_1 = 'Queuing1'
QUEUE_2 = 'Queuing2'
LOSS_1 = 'Losses1'
LOSS_2 = 'Losses2'

################################
#     COMMON FUNCTION USED     #
################################

def get_dir_from_arg(directory, end=''):
    # Credits : M. Baerts & Q. De Coninck in mptcp-analysis-scripts
    """ Get the abspath of the dir given by the user and append 'end' """
    if end.endswith('.'):
        end = end[:-1]

    if directory.endswith('/'):
        directory = directory[:-1]

    return os.path.abspath(os.path.expanduser(directory)) + end

def check_directory_exists(directory):
	# Credits : M. Baerts & Q. De Coninck in mptcp-analysis-scripts
    """ Check if the directory exists, and create it if needed
        If directory is a file, exit the program
    """
    if os.path.exists(directory):
        if not os.path.isdir(directory):
            print(directory + " is a file: stop")
            sys.exit(1)

    else:
        os.makedirs(directory)
        
def experiment_one_topo(factor, dirpath, xp_file):
    name_xp_dir = str(factor[CAPA_1])+'_'+str(factor[DELAY_1])+'_'+\
                str(factor[QUEUE_1]) +'-'+ str(factor[CAPA_2])+'_'+\
                str(factor[DELAY_2])+'_'+str(factor[QUEUE_2])

    path_xp_dir = os.path.join(dirpath, name_xp_dir)
    check_directory_exists(path_xp_dir)

    topo_factor_file = os.path.join(path_xp_dir, 'topo')
	
    copyfile(topo_file,topo_factor_file)
    with open(topo_factor_file, 'a') as topo_factor:
        topo_factor.write('path_0:'+str(factor[DELAY_1])+','+\
                str(factor[QUEUE_1])+','+str(factor[CAPA_1])+',0\n')
        topo_factor.write('path_1:'+str(factor[DELAY_2])+','+\
                str(factor[QUEUE_2])+','+str(factor[CAPA_2])+',0\n')
   	
    os.chdir(path_xp_dir)
    
    call(['sudo', bin_mpPerf, '-t', topo_factor_file, '-x', xp_file])
    
def experiment_one_topo_one_path(factor, dirpath, xp_file):
    name_xp_dir = str(factor[CAPA_1])+'_'+str(factor[DELAY_1])+'_'+\
                str(factor[QUEUE_1]) 

    path_xp_dir = os.path.join(dirpath, name_xp_dir)
    check_directory_exists(path_xp_dir)

    topo_factor_file = os.path.join(path_xp_dir, 'topo')
	
    copyfile(topo_file,topo_factor_file)
    with open(topo_factor_file, 'a') as topo_factor:
        topo_factor.write('path_0:'+str(factor[DELAY_1])+','+\
                str(factor[QUEUE_1])+','+str(factor[CAPA_1])+',0')
   	
    os.chdir(path_xp_dir)
    
    call(['sudo', bin_mpPerf, '-t', topo_factor_file, '-x', xp_file])

    name_xp_dir = str(factor[CAPA_2])+'_'+str(factor[DELAY_2])+'_'+\
                str(factor[QUEUE_2]) 

    path_xp_dir = os.path.join(dirpath, name_xp_dir)
    check_directory_exists(path_xp_dir)

    topo_factor_file = os.path.join(path_xp_dir, 'topo')
	
    copyfile(topo_file,topo_factor_file)
    with open(topo_factor_file, 'a') as topo_factor:
        topo_factor.write('path_0:'+str(factor[DELAY_2])+','+\
                str(factor[QUEUE_2])+','+str(factor[CAPA_2])+',0')
   	
    os.chdir(path_xp_dir)
    
    call(['sudo', bin_mpPerf, '-t', topo_factor_file, '-x', xp_file])
    
def experiment_one_topo_loss(factor, dirpath, xp_file):
    name_xp_dir = str(factor[CAPA_1])+'_'+str(factor[DELAY_1])+'_'+str(factor[QUEUE_1])+'_'+str(factor[LOSS_1])+'-'
    name_xp_dir = name_xp_dir + str(factor[CAPA_2])+'_'+str(factor[DELAY_2])+'_'+str(factor[QUEUE_2])+'_'+str(factor[LOSS_2])

    path_xp_dir = os.path.join(dirpath, name_xp_dir)
    check_directory_exists(path_xp_dir)

    topo_factor_file = os.path.join(path_xp_dir, 'topo')
	
    copyfile(topo_file,topo_factor_file)
    with open(topo_factor_file, 'a') as topo_factor:
        topo_factor.write('path_0:'+str(factor[DELAY_1])+','+str(factor[QUEUE_1])+','+str(factor[CAPA_1])+','+str(factor[LOSS_1])+'\n')
        topo_factor.write('path_1:'+str(factor[DELAY_2])+','+str(factor[QUEUE_2])+','+str(factor[CAPA_2])+','+str(factor[LOSS_2])+'\n')
   	
    os.chdir(path_xp_dir)
    
    call(['sudo', bin_mpPerf, '-t', topo_factor_file, '-x', xp_file])
    
def experiment_one_topo_loss_one_path(factor, dirpath, xp_file):
    name_xp_dir = str(factor[CAPA_1])+'_'+str(factor[DELAY_1])+'_'+str(factor[QUEUE_1])+'_'+str(factor[LOSS_1])

    path_xp_dir = os.path.join(dirpath, name_xp_dir)
    check_directory_exists(path_xp_dir)

    topo_factor_file = os.path.join(path_xp_dir, 'topo')
	
    copyfile(topo_file,topo_factor_file)
    with open(topo_factor_file, 'a') as topo_factor:
        topo_factor.write('path_0:'+str(factor[DELAY_1])+','+str(factor[QUEUE_1])+','+str(factor[CAPA_1])+','+str(factor[LOSS_1])+'\n')
   	
    os.chdir(path_xp_dir)
    
    call(['sudo', bin_mpPerf, '-t', topo_factor_file, '-x', xp_file])

    name_xp_dir = str(factor[CAPA_2])+'_'+str(factor[DELAY_2])+'_'+str(factor[QUEUE_2])+'_'+str(factor[LOSS_2])

    path_xp_dir = os.path.join(dirpath, name_xp_dir)
    check_directory_exists(path_xp_dir)

    topo_factor_file = os.path.join(path_xp_dir, 'topo')
	
    copyfile(topo_file,topo_factor_file)
    with open(topo_factor_file, 'a') as topo_factor:
        topo_factor.write('path_0:'+str(factor[DELAY_2])+','+str(factor[QUEUE_2])+','+str(factor[CAPA_2])+','+str(factor[LOSS_2])+'\n')
   	
    os.chdir(path_xp_dir)
    
    call(['sudo', bin_mpPerf, '-t', topo_factor_file, '-x', xp_file])
