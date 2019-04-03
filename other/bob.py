#!/usr/bin/python3
"""
Script to build projects using NQBP
===============================================================================
usage: bob [options] here [<nqbp-opts>...]
       bob [options] PATTERN [<nqbp-opts>...]
       bob [options] --file BLDLIST

Options:
    here                 Builds all NQBP projects starting from the current 
                         working directory.
    <nqbp-opts>          Option(s) to be passed directly to NQBP
    PATTERN              If a subdir under PRJDIR matches PATTERN, then that
                         directory is built.  Standard Python wildcards can
                         be used in the PATTERN.
    --path PRJDIR        The full path to the project directory of the 
                         projects to build.  If no path is specified, the
                         current working directory is used for the project
                         path.
    --file BLDLIST       A text file containing a list of projects to build.
                         The format of file is a list of 'build' commands. 
                         Blank lines and line starting with '#' are skipped.
    --xconfig SCRIPT     Name and full path to the compiler config script.  If 
                         no script is provided then it is assume no additional 
                         config/setup is required.
    --config SCRIPT      Same as the '--xconfig' option, but the name and path 
                         are relative to the package root directory
    -v                   Be verbose 
    -h, --help           Display help for common options/usage
    
Examples:
    ; Builds all NQBP projects (and all 'variants') under the projects/ 
    ; directory that contain 'mingw' in their path.  The '--bld-all' option 
    ; is NQBP option.
    build --path \mywrkspace\mypkg\projects mingw --bld-all
    
    ; Builds the projects listed in the file 'mybuild.lst'
    build --file mybuild.lst
    
"""

import sys
import os
import subprocess
import fnmatch

sys.path.append( os.path.dirname(__file__) + os.sep + ".." )
from docopt.docopt import docopt
from nqbplib import utils
from nqbplib import my_globals

BOB_VERSION = '1.0'

#------------------------------------------------------------------------------
def _filter_prj_list( all_prj, pattern, pkgroot ):
    list = []
    for p in all_prj:
        relpath = p.replace(pkgroot,'')
        dirs    = relpath.split(os.sep)
        if ( len(fnmatch.filter(dirs,pattern))> 0 ):
            list.append( p )
            

    return list
    
def _build_project( prjdir, verbose, bldopts, config, xconfig, pkgroot ):
    # reconcile config options
    cfg = None
    if ( config ):
        cfg = os.path.join( pkgroot, config )
    elif ( xconfig ):
        cfg = xconfig
    
    # Build the project
    utils.push_dir( os.path.dirname(prjdir) )
    print("BUILDING: "+ prjdir)
    cmd = 'nqbp.py ' + " ".join(bldopts)
    if ( config ):
        cmd = utils.concatenate_commands( cfg, cmd )
    utils.run_shell( cmd, verbose, "ERROR: Build failure ({})".format(cmd) )
    utils.pop_dir()




#------------------------------------------------------------------------------
# BEGIN
if __name__ == '__main__':

    # Parse command line
    args = docopt(__doc__, version=BOB_VERSION, options_first=True )
    
    # Set quite & verbose modes
    utils.set_verbose_mode( args['-v'] )

    # Default the projects/ dir path to the current working directory
    ppath = os.getcwd()
    
    # Project dir path is explicit set
    if ( args['--path'] ):
        ppath = args['--path']

    
    # Get superset of projects to build
    utils.push_dir( ppath )
    utils.set_pkg_and_wrkspace_roots( ppath )    
    pkgroot = NQBP_PKG_ROOT()
    all_prjs = utils.walk_file_list( "nqbp???", ppath )

    # Get project list from a file
    if ( args['--file'] ):
        try:
            inf = open( args['--file'], 'r' )

            # process all entries in the file        
            for line in inf:
               
                # drop comments and blank lines
                line = line.strip()
                if ( line.startswith('#') ):
                    continue
                if ( line == '' ):
                    continue
           
                # 'normalize' the file entries
                line = utils.standardize_dir_sep( line.strip() )
        
                # Process 'add' entries
                cmd = "bob.py " + line
                utils.run_shell( cmd, args['-v'], "ERROR: Build from File failed." )
    
            inf.close()
        
        except Exception as ex:
            exit( "ERROR: Unable to open build list: {}".format(args['--file']) )
        
    

    # The project list is from the command line
    else:
        # Only build the projects that match the pattern
        pattern = args['PATTERN']
        if ( args['here'] ):
            pattern = '*'
    
        for p in _filter_prj_list( all_prjs, pattern, pkgroot ):
            _build_project(p, args['-v'], args['<nqbp-opts>'], args['--config'], args['--xconfig'], pkgroot )

    # restore original cwd
    utils.pop_dir()
    
