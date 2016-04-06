#!/usr/bin/env python
import os
import subprocess
from glob import iglob, glob

'''print (folder_name, total_rst7, restrained_rst7, non_restrained_rst7)
'''

folders = [fn for fn in iglob('./*') if os.path.isdir(fn)]


folders_with_num = []
for fn in folders:
    min_restraints = glob('{}/min*rst7'.format(fn))
    min_no_restraints = glob('{}/no_restraint/min*rst7'.format(fn))
    total_rst7 = glob('{}/NoH_*rst7'.format(fn))
    folders_with_num.append([fn.replace('./', ''), len(total_rst7), len(
        min_restraints), len(min_no_restraints)])

sorted_folders_with_num = sorted([folder for folder in folders_with_num if folder[
                        1:] != [0, 0, 0]], key=lambda x: -2 * x[1] + x[2] + x[3])

def get_running_jobs():
    _running_jobs = subprocess.check_output(
        "squeue |grep hn120 | awk '{print $3}'",
        shell=True).split()
    
    running_jobs = set(x.split('.')[0] for x in _running_jobs)
    print('running_jobs', running_jobs)
    print("\n\n")

    return running_jobs
    
def get_restart_files_count(sorted_folders_with_num):
    for folder in sorted_folders_with_num:
        yield tuple(folder)

def need_to_run(running_jobs):
    will_be_submitted = set(x[0].strip(
        './') for x in sorted_folders_with_num if 2 * x[1] - x[2] - x[3] > 0) - running_jobs
    
    joint_jobs = ','.join(will_be_submitted)

    msg_ = 'good to copy and paste to run = {}'
    msg = msg_.format(joint_jobs) if joint_jobs else msg_.format('None')
    print(msg)

def get_all_finished_runs(sorted_folders_with_num):
    return set(x[0].strip('./')
               for x in sorted_folders_with_num if x[1] == x[2] == x[3] and x[2] > 0)

def get_unfinished_folders(folders):
    '''get not-run yet files or file has size of 0. Use absolute path
    '''
    folder_having_zero_size_rst7 = []

    for folder in folders:
        for fn in iglob(folder + '/min*rst7'):
            if os.path.getsize(fn) < 1000:
                folder_having_zero_size_rst7.append(folder.strip('./'))
                break

    unfinised_folders = set(get_unfinished_folders(folders)) - running_jobs
    print('unfinised_folders\n')
    print(','.join(unfinised_folders))

def check_missing_runs(restart_count_tuple, given_list):
    code_and_file_count_dict = {}

    for code_tuple  in restart_count_tuple:
        code_and_file_count_dict[code_tuple[0]] = code_tuple
    for code in given_list:
        try:
            code_and_file_count_dict[code]
        except KeyError:
            print('missing {}'.format(code))

if __name__ == '__main__':
    restart_count_tuple = list(get_restart_files_count(sorted_folders_with_num))
    for count_tuple in restart_count_tuple:
        print(count_tuple)
    running_jobs = get_running_jobs()
    print('total number of folders = {}'.format(len(folders)))
    need_to_run(running_jobs)

    given_list = """1t2p
    2ppp
    2dfb
    1tud
    2h3l
    2igd
    1vkk
    2a28
    2icp
    2gzv
    1opd
    2nwd
    2cxd
    1ubi
    2zib
    1vcc
    1igd
    1ifb
    1iib.decoys.set1""".split()
    # check_missing_runs(restart_count_tuple, given_list)
