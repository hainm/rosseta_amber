#!/usr/bin/env python
import os, sys
import subprocess
from glob import iglob, glob

'''print (folder_name, total_rst7, restrained_rst7, non_restrained_rst7)
'''

folders = [fn for fn in iglob('./*') if os.path.isdir(fn)]


folders_with_num = []
for fn in folders:
    min_restraints = glob('{}/min*rst7'.format(fn))
    min_no_restraints = glob('{}/no_restraint/min*rst7'.format(fn))
    min_99sbigb1_restraints = glob('{}/99sb_igb1/res*new*/min*rst7'.format(fn))
    min_99sbigb1_no_restraints = glob('{}/99sb_igb1/no*res*new*/min*rst7'.format(fn))
    total_rst7 = glob('{}/NoH_*rst7'.format(fn))
    folders_with_num.append([fn.replace('./', ''), len(total_rst7), len(
        min_restraints), len(min_no_restraints), len(min_99sbigb1_restraints), len(min_99sbigb1_no_restraints)])

sorted_folders_with_num = sorted([folder for folder in folders_with_num 
    if folder[1:] != [0, 0, 0, 0, 0]],
    key=lambda x: -4 * x[1] + sum(x[2:]))

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

def need_to_run(running_jobs, ignore_running_job=False):
    if not ignore_running_job:
        will_be_submitted = set(x[0].strip(
            './') for x in sorted_folders_with_num if 4 * x[1] - sum(x[2:]) > 0) - running_jobs
    else:
        will_be_submitted = [x[0].strip(
            './') for x in sorted_folders_with_num if 4 * x[1] - sum(x[2:]) > 0]
    
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
    try:
        sys.argv.remove('--ignore-running-job')
        ignore_running_job = True
    except ValueError:
        ignore_running_job = False
    restart_count_tuple = list(get_restart_files_count(sorted_folders_with_num))
    for count_tuple in restart_count_tuple:
        print(count_tuple)

    print('4th run is finished')
    print(set(count_tuple[0] for count_tuple in restart_count_tuple if count_tuple[1] == count_tuple[4]))

    running_jobs = get_running_jobs()
    print('total number of folders = {}'.format(len(folders)))
    need_to_run(running_jobs, ignore_running_job)

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
