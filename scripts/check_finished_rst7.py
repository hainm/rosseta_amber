#!/usr/bin/env python
import os
import subprocess
from glob import iglob, glob

'''print (folder_name, total_rst7, restrained_rst7, non_restrained_rst7)
'''

folders = [fn for fn in iglob('./*')  if os.path.isdir(fn)]

_codes = '3ess,2he4,2acy,1tig,2wwe,1poh,1wdv,3q6l,1prq,1fna,2chf,1tul,1z2u,1zma,1t3y,1o8x,1sau,2hhg,3co1,1x6x,1t2i,3hp4,1jbe,2nqw,2jek,3d4e'.split(',')

already_sent_to_Kristin = set(['3ey6', '3f2z', '3fk8', '3hyn', 
                               '3dke', '3gbw', '2qsk', '1mjc'] + _codes)

folders_with_num = []
for fn in folders:
    min_restraints = glob('{}/min*rst7'.format(fn))
    min_no_restraints = glob('{}/no_restraint/min*rst7'.format(fn))
    total_rst7 = glob('{}/NoH_empty_tag_*rst7'.format(fn))
    folders_with_num.append([fn, len(total_rst7), len(min_restraints), len(min_no_restraints)])

sorted_folders = sorted([folder for folder in folders_with_num if folder[1:] != [0, 0, 0]], key=lambda x: x[3])

for folder in sorted_folders:
    print(tuple(folder))

print('top 10')
print(','.join((x[0].strip('./') for x in sorted_folders[:10] if x[1] > 0)))

print('\n\n')
print('finished')

all_done = set(x[0].strip('./')  for x in sorted_folders if x[1] == x[2] == x[3] and x[2] > 0)
print(all_done)

print('already sent to Kristin')
print(already_sent_to_Kristin)

print('need to send to Kristin')
code_string = ','.join(all_done - already_sent_to_Kristin)
print('decoys.set1.init/{' + code_string + '}')
