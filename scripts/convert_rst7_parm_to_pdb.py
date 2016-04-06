import pytraj as pt
import sys

def main(argv):
    args = sys.argv
    pdb = args[0].rstrip('.pdb')
    # restart file
    rst7 = 'min_%s.rst' % pdb

    # parm
    parm = '%s.parm7' % pdb

    # save
    traj = pt.iterload(rst7, parm)
    traj.save('min_%s.pdb' % pdb )

if __name__ == "__main__":
    main(sys.argv[1:])
