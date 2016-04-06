import pytraj as pt

# choose all but H atoms
mask = '!@H='

# amber mask: http://amber-md.github.io/pytraj/latest/atom_mask_selection.html

pdblist = ['fn1.pdb', 'fn2.pdb']

for pdb in pdblist:
    traj = pt.iterload(pdb)
    traj[mask].save('strip_h_' + pdb)
