import os, sys, getopt, math, time

PATH_TO_DECOYDISC = "/project1/dacase-001/haichit/rosseta_amber/DecoyDiscrimination/"
ROSETTA_BIN = PATH_TO_DECOYDISC+"/extract_pdbs.static.linuxgccrelease"
ROSETTA_DB = PATH_TO_DECOYDISC+"/Rosetta_Database/"
AMBER_HOME = os.environ.get("AMBERHOME")

def chunks(l,n):
    n = max(1,n)
    return [l[i:i+n] for i in range(0, len(l), n)]

def main(argv):
    args = sys.argv

    input_pdb = ''
    num_total_jobs = -1
    num_mins_per_job = -1
    decoy_set_index = 0
    min_script = ''

    try:
        opts, args=getopt.getopt(sys.argv[1:], "ho:n:t:p:d:m:", ["in:file:native=", "total_num_jobs=", "num_minimizations_per_job=", "decoy_set=", "minimization_script="])
    except getopt.GetoptError:
        print('Unknown flag given.\nKnown flags:\n\t-h\n\t-n <native_pdb_id>')
        sys.exit()

    for opt, arg in opts:
        if opt == '-h':
            print('ConvertToPDBandSubmitMinimizationJobs.py --in:file:n <input_pdb_id> --total_num_jobs #\nor\nConvertToPDBandSubmitMinimizationJobs.py --in:file:n <input_pdb_id> --num_minimizations_per_job #')
            sys.exit()
        elif opt in ("-n", "--in:file:native"):
            input_pdb = arg
        elif opt in ("-t", "--total_num_jobs"):
            num_total_jobs = int(arg)
        elif opt in ("-p", "--num_minimizations_per_job"):
            num_mins_per_job = int(arg)
        elif opt in ("-d", "--decoy_set"):
            decoy_set_index = int(arg)
        elif opt in ("-m", "--minimization_script"):
            min_script = arg

    if input_pdb == '':
        print('ERROR: No input pdb supplied.')
        sys.exit()
    else:
        print('input_pdb', input_pdb)
        input_pdb = input_pdb.replace('.pdb', '').lower()
        print('input_pdb', input_pdb)

    if min_script == '':
        print("ERROR: No minimization script specified.")
        sys.exit()

    if num_total_jobs >= 0 and num_mins_per_job >= 0:
        print("ERROR: Both --total_num_jobs and --num_minimizations_per_job given.")
        sys.exit()

    if num_total_jobs == -1 and num_mins_per_job == -1:
        num_mins_per_job = 40

    print( "===== Native: %s =====" % input_pdb )
    if num_total_jobs > -1:
        print("A total of %i jobs will be submitted to the queue." % num_total_jobs)
    else:
        print("Each job will contain a maximum of %i minimization jobs(s)." % num_mins_per_job)

    #####################################
    ### Create PDBs from Silent Files ###
    #####################################
    print( "\t===== Creating PDBs from Silent File =====" )
    
    ## Decoy Set 1 or Set 2? ##
    if decoy_set_index == 1:
        decoy_set = "decoys.set1.init"
        file_ending = "1000.out"
    else:
        decoy_set = "decoys.set2.init"
        file_ending = "retag.nocartbump.out"

    ## Has the silent file been extracted before? If so, make a new working directory in the old directory so we do not overwrite. ##
    dt = ''
    if not os.path.exists( "%s/%s/%s/" % ( PATH_TO_DECOYDISC, decoy_set, input_pdb )):
        os.mkdir( "%s/%s/%s/" % ( PATH_TO_DECOYDISC, decoy_set, input_pdb ) )
        os.chdir( "%s/%s/%s/" % ( PATH_TO_DECOYDISC, decoy_set, input_pdb ) )
        
        ## Copy Native to working directory. ##
        os.system("cp %s/Natives/%s_0001.clean.pdb ." % (PATH_TO_DECOYDISC, input_pdb ))

    else:
        print( "WARNING: %s/%s/%s EXISTS." % ( PATH_TO_DECOYDISC, decoy_set, input_pdb ) )
        dt = time.strftime("%y%m%d.%H%M%S")
        print( "Making new working directory for this minimization run...%s/%s/%s/%s" % (PATH_TO_DECOYDISC, decoy_set, input_pdb, dt) )
        os.mkdir( "%s/%s/%s/%s/" % ( PATH_TO_DECOYDISC, decoy_set, input_pdb, dt ) )
        os.chdir( "%s/%s/%s/%s/" % ( PATH_TO_DECOYDISC, decoy_set, input_pdb, dt ) )
        #sys.exit()
    
    if dt == '':
        os.system( "%s -database %s -in:file:silent %s/%s/%s.%s" % (ROSETTA_BIN, ROSETTA_DB, PATH_TO_DECOYDISC, decoy_set, input_pdb, file_ending ) )
        decoys = os.popen('ls empty*.pdb').readlines()  ## List of pdbs ["<pdb1>\n", "<pdb2>\n", ...]
        
        ##################################
        ### Remove Hydrogens from PDBs ###
        ##################################
        no_h_decoys = []
        for pdb in decoys:
            os.system("sed '/     H  /d' %s > NoH_%s" % ( pdb.rstrip(), pdb.rstrip() ) )
            no_h_decoys.append('NoH_%s' % pdb.rstrip())

        ##################################################
        ### Create RST7 and PARM7 files from NoH_PDBs. ###
        ##################################################
        with open('tleap.in','w') as tfile:
            tfile.write("source leaprc.ff14SBonlysc\n")
            tfile.write("m = loadpdb @@@.pdb\n")
            tfile.write("set default pbradii mbondi3\n")
            tfile.write("saveamberparm m %s.parm7 @@@.rst7\n" % input_pdb)
            tfile.write("quit")

        for pdb in no_h_decoys:
            os.system('sed "s/@@@/%s/g" tleap.in > %s.tleap.in' % ( pdb.rstrip('.pdb\n'), pdb.rstrip('.pdb\n') ) )
            os.system('tleap -f %s.tleap.in' % ( pdb.rstrip('.pdb\n') ) )

    else:
        no_h_decoys = os.popen('ls %s/%s/%s/NoH_*.pdb' % (PATH_TO_DECOYDISC, decoy_set, input_pdb) ).readlines()
        for i in range(len(no_h_decoys)):
            no_h_decoys[i] = no_h_decoys[i].rstrip()
    ######################################
    ### Generate Minimization Commands ###
    ######################################
    minimization_commands = []
    for pdb in no_h_decoys:

        if dt != '':
            min_rst7 = "/".join(pdb.split('/')[0:-1]) + "/" + dt + "/min_"+pdb.split('/')[-1].rstrip('.pdb\n')+'.rst7'
            min_out = "/".join(pdb.split('/')[0:-1]) + "/" + dt + "/min_"+pdb.split('/')[-1].rstrip('.pdb\n')+'.out'
        
        else:
            min_rst7 = "min_" + pdb.rstrip('.pdb\n') + ".rst7"
            min_out = "min_" + pdb.rstrip('.pdb\n') + ".out"
       
        minimization_commands.append('sander -O -i %s -o %s -p %s/%s/%s/%s.parm7 -c %s.rst7 -r %s -ref %s.rst7\n' % ( min_script, min_out, PATH_TO_DECOYDISC, decoy_set, input_pdb, input_pdb, pdb.rstrip('.pdb\n'), min_rst7, pdb.rstrip('.pdb\n') ) )


    #################################
    ##### Submit to Slurm Queue #####
    #################################
    if num_total_jobs > -1:
        num_mins = int( math.ceil( float(len(minimization_commands) )/float(num_total_jobs) ) )
        minimization_chunks = chunks(minimization_commands, num_mins)
        print("Submitting %i jobs with a maximum of %i minimization job(s) per script." % ( num_total_jobs, num_mins) )

    else:
        minimization_chunks = chunks(minimization_commands, num_mins_per_job)
        print("Submitting %i jobs with a maximum of %i minimization jobs(s) per script." % ( len(minimization_chunks), num_mins_per_job ) )

    file_count = 0
    for minchunk in minimization_chunks:
        file_count += 1
        with open( 'MinimizationScript%i.sh' % file_count, 'w' ) as minfile:
            minfile.write("#!/bin/bash\n#SBATCH -n 1\n#SBATCH -c 1\n#SBATCH -o MinimizationScript%i.out\n#SBATCH --job-name=%sM%i\n\nsource %s/amber.sh\n\n" % ( file_count, input_pdb, file_count, AMBER_HOME ) )
            for minimization_command in minchunk:
                minfile.write(minimization_command)
        # os.system('sbatch MinimizationScript%i.sh' % file_count)
    ################################

if __name__ == "__main__":
    main(sys.argv[1:])
