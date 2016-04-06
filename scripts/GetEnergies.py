import pytraj as pt
import sander
import os, sys, getopt

PATH_TO_DECOYDISC = "/scratch/kmb413/RealDecoyDisc/DecoyDiscrimination/decoys.set2.init/1aaj/Rosetta_relaxed"

def chunks(l,n):
    n = max(1,n)
    return [l[i:i+n] for i in range(0, len(l), n)]

def main(argv):
    args = sys.argv

    native = ''
    outfile = ''

    try:
        opts, args=getopt.getopt(sys.argv[1:], "ho:n:o:", ["in:file:n=", "out:file:scorefile="])
    except getopt.GetoptError:
        print('Unknown flag given.\nKnown flags:\n\t-h\n\t-n <native>')
        sys.exit()

    for opt, arg in opts:
        if opt == '-h':
            print('Something.py --in:file:s <input_pdb_id> --out:file:scorefile <output_filename>')
            sys.exit()
        elif opt in ("-n", "--in:file:n"):
            native = arg
        elif opt in ("-o", "--out:file:scorefile"):
            outfile = arg

    if native == '':
        print('No native rst7 supplied.')
        sys.exit()

    if outfile == '':
        outfile = 'Scores.sc'

    print( "===== Native RST7: %s =====" % native )

    os.chdir(PATH_TO_DECOYDISC)
    min_decoys = os.popen('ls min*.rst7').readlines()  ## List of rst7s ["<rst7_1>\n", "<rst7_2>\n", ...]
    for m in range(len(min_decoys)):
        min_decoys[m] = min_decoys[m].rstrip()

    if native in min_decoys:
        min_decoys.remove(native)

    print("== Analyzing %i mols==" % len(min_decoys))

    min_decoys.insert(0, native)
    parmfile = '_'.join(native.split('_')[1:]).rstrip('rst7') + 'parm7'

    print("\t=== Loading Trajectories ===")
    traj = pt.iterload(min_decoys, parmfile)

    print("\t=== Getting RMSDs ===")
    ca_rmsd_data = pt.rmsd(traj, mask=['@CA'])

    print("\t=== Getting Energy Decomposition ===")
    energy_data = pt.energy_decomposition(traj, igb=8)
    print("\t\tFinished")

    with open(outfile,'w') as scorefile:
        header = 'pdb\t'
        for s in energy_data.keys():
            header += s + '\t'
        header += 'rmsd\n'
        scorefile.write(header)

        for pdb_index in range(len(min_decoys)):
            scoreline = min_decoys[pdb_index]+'\t'
            for s in energy_data.keys():
                scoreline += '%s\t' % str(energy_data[s][pdb_index])
            scoreline += '%s\n' % str(ca_rmsd_data[pdb_index])
            scorefile.write(scoreline)

if __name__ == "__main__":
    main(sys.argv[1:])
