""" Top level entry point for NQBP (i.e. called by the project-being-built's mk.py) """

#=============================================================================
# ENVIRONMENT VARIABLES
# ---------------------
#   REQUIRED:
#     NQBP_BIN          Path to the directory of where (and/or which version)
#                       of the NQBP Python package to be used
#
#   OPTIONAL:
#
#=============================================================================

#
import sys   
import os
import logging
import time
#
from nqbplib.docopt.docopt import docopt
from base import ToolChain
import base
import utils

    
# Globals
from my_globals import NQBP_WORK_ROOT
from my_globals import NQBP_PKG_ROOT
from my_globals import NQBP_TEMP_EXT
from my_globals import NQBP_VERSION
from my_globals import NQBP_PRJ_DIR
from my_globals import NQBP_NAME_LIBDIRS
from my_globals import NQBP_WRKPKGS_DIRNAME
from my_globals import NQBP_NAME_SOURCES


# 
usage = """ 
(N)ot (Q)uite (B)env/(P)ython Build Script
===============================================================================
Usage: nqbp [options] [-b variant] 
       nqbp [options] [-b variant] -d DIR
       nqbp [options] [-b variant] -f FILE
       nqbp [options] [-b variant] -s DIR
       nqbp [options] [-b variant] -m [-d DIR | -f FILE]

Arguments:
  -b variant       Builds the speficied configuration/varinst instead of the 
                   release build. What 'variants' are available is Toolchain 
                   specific. The default is variant is determined by the
                   mytoolchain.py script.
  --bld-all        Builds all variants.  Does NOT build variants that start 
                   with a leading '_'.
  -d DIR           Compile ONLY the specified directory relative to the pkg 
                   root. If 'DIR' starts with a directory seperator ('\\' or 
                   '/') then the directory is relative to the package root. If
                   'DIR' starts with a double directory seperator ('\\\\' or
                   '//') then the directory is relative to the workspace root.
  -f FILE          Compile ONLY the specified file relative to the pkg root.
                   If 'FILE' starts with a directory seperator ('\\' or '/'
                   then the file is relative to the package root. If 'FILE' 
                   starts with a double directory seperator ('\\\\' or
                   '//') then the file is relative to the workspace root. A 
                   'FILE' in the project directory can be compile by prefixing 
                   'FILE' with './' or '.\\' (i.e. current directory).
  -s DIR           Skips all entries in libdirs.b BEFORE 'DIR', i.e. start with 
                   'DIR'.  Note: 'DIR' is with respect to the expanded list of 
                   directories, i.e. after any included libdirs.b files are 
                   expanded.
  -e DIR           Skip all entries in libdirs.b AFTER 'DIR', i.e. stop 
                   building directories once 'DIR' has been built. Note: 'DIR' 
                   is with respect to the expanded list of directories, i.e. 
                   after any included libdirs.b files are expanded.
  -p               Skips all external directories and/or libdirs.b files.
  -x               Skips all the package's directories and/or libdirs.b files
  -m               Compiles all of the project directory.
  -g               Debug build (default is release build.
  -v               Display Compiler/linker options.
  -l               Link ONLY (can be combinded with '-mpxdfse' options).
  -k               Cleans only the package's objects/files (use with '-p')
  -j               Cleans only the external objects/files (use with '-x').
  -z, --clean-all  Cleans ALL files for ALL build configurations and then exits
  --debug          Enables debug info internally to NQBP.
  --qry            Outputs the current project directory (does nothing else)
  --qry-and-clean  Combines '--qry' and '--clean-all' options into a single 
                   operation.
  --qry-blds       Displays the build 'variants' supported by the toolchain 
                   (no build is performed).
  -h,--help        Display help.
  --version        Display version number.

Notes:
    Default operation is to do an implicit BUILD ALL and CLEAN ALL on each 
    build.  The exception to this rule is when one of the following options are  
    specified: -d, -f, -s, -e, -p, -x, -m, -l, -k, -j   
         
Examples:

"""


#-----------------------------------------------------------------------------
def build( argv, toolchain ):

    # ensure that I am executing in the project directory
    os.chdir( NQBP_PRJ_DIR() )

    # Process command line args...
    arguments = docopt(usage, version=NQBP_VERSION() )
    
    # Set default build variant 
    if ( not arguments['-b'] ):
        arguments['-b'] = toolchain.get_default_variant()
    
    
    # Pre-build steps
    pre_build_steps( toolchain, arguments )
    utils.debug( arguments )

    # Process 'non-build' options
    if ( arguments['--qry-blds'] ):
        toolchain.list_variants()
        sys.exit()
    
    if ( arguments['--qry'] ):
        utils.output( '%s', NQBP_PRJ_DIR() )
        sys.exit()
       
    if ( arguments['--qry-and-clean'] ):
        utils.output( "%s", NQBP_PRJ_DIR() )
        toolchain.clean_all( arguments, silent=True )
        utils.remove_log_file()
        sys.exit()
    
    if ( arguments['--clean-all'] ):
        toolchain.clean_all( arguments )
        utils.remove_log_file()
        sys.exit()
        
    # Validate Compiler toolchain is set properly (ONLY after non-build options have been processed, i.e. don't have to have an 'active' toolchain for non-build options to work)
    toolchain.validate_cc()
        
    # Start the selected build(s)
    if ( arguments['--bld-all'] ):
        for b in toolchain.get_variants():
            if ( not b.startswith("_") ):
                do_build( toolchain, arguments, b )
    else: 
        do_build( toolchain, arguments, arguments['-b'] )        
            
           

#-----------------------------------------------------------------------------
def do_build( toolchain, arguments, variant ):
    # Set the build variant
    toolchain.pre_build( variant, arguments )

    # Output start banner
    start_banner(toolchain)
     
    # Spit out handy-dandy debug info
    utils.debug( '# NQBP version   = ' + NQBP_VERSION() )
    utils.debug( '# NQBP_BIN       = ' + os.path.dirname(os.path.abspath(__file__)) )
    utils.debug( '# NQBP_WORK_ROOT = ' + NQBP_WORK_ROOT() )
    utils.debug( '# NQBP_PKG_ROOT  = ' + NQBP_PKG_ROOT() )
    utils.debug( '# Project Dir    = ' + NQBP_PRJ_DIR() )
    
    # Create/expand my working libdirs.b file
    libdirs = []
    inf = open( NQBP_NAME_LIBDIRS(), 'r' )
    utils.create_working_libdirs( inf, arguments, libdirs, 'local', variant )  
    inf.close()
    utils.list_libdirs( libdirs )
    
    # Set default operations
    clean_pkg = True
    clean_ext = True
    bld_prj   = True
    do_link   = True
    bld_libs  = True
    stop      = False
    
    # Skip cleaning when selective building of libdirs.b
    if ( arguments['-p'] or arguments['-x'] or arguments['-s']  or arguments['-e']):
        clean_pkg = clean_ext = False
        
    # Compile only a single file    
    if ( arguments['-f'] ):
        clean_pkg = clean_ext = bld_prj = do_link = bld_libs = False
        build_single_file( arguments, toolchain )
        
    # Compile only a single directory    
    if ( arguments['-d'] ):
        clean_pkg = clean_ext = bld_prj = do_link = bld_libs = False
        dir       = utils.standardize_dir_sep( arguments['-d'] )
        entry     = 'local'

        # Trap directory is relative to the package root
        if ( dir.startswith(os.sep) ):
            dir   = dir[1:]
            entry = 'pkg'
            
        # Trap directory is relative to the workspace root
        elif ( dir.startswith(os.sep+os.sep) ):
            dir     = dir[2:]
            entry   = 'xpkg'
                                              
        # special case of relative to the workspace
        elif ( dir.startswith(NQBP_WRKPKGS_DIRNAME()) ):
            dir     = dir[len(NQBP_WRKPKGS_DIRNAME())+1:]
            entry   = 'xpkg'
            
        build_single_directory( arguments, toolchain, dir, entry )
        
    # Trap compile just the project directory
    if ( arguments['-m'] ):
        clean_pkg = clean_ext = do_link = bld_libs = False
        bld_prj   = True
    
    # Trap link only flag
    if ( arguments['-l'] ):
        do_link   = True
        clean_pkg = clean_ext = bld_libs = bld_prj = False

        # fix race condition between the -l and -m options
        if ( arguments['-m'] or arguments['-x'] or arguments['-p']  ):
            bld_prj = True
            
        # fix race condition between the -l and -px options
        if ( arguments['-x'] or arguments['-p'] ):
            bld_libs = True

    # Trap the clean options 
    if ( arguments['-k'] ):
        clean_pkg = True
        if ( not arguments['-j'] ):
            clean_ext = False
    if ( arguments['-j'] ):
        clean_ext = True
        if ( not arguments['-k'] ):
            clean_pkg = False
        
            
                        
    # Clean before the build starts
    toolchain.clean( clean_pkg, clean_ext )
    
    # Build libdirs.b
    if ( bld_libs ):
        
        # Filter directories when '-s' option is used
        if ( arguments['-s'] ):
            skip     = True
            startdir = utils.standardize_dir_sep( arguments['-s'] )
            
            # Trap special case of using 'xpkgs' directory
            if ( startdir.startswith(NQBP_WRKPKGS_DIRNAME()) ):
                startdir = os.sep + startdir[len(NQBP_WRKPKGS_DIRNAME())+1:]
            
        else:
            skip     = False
            startdir = ''
        
        # Filter directories when '-e' option is used
        stopdir = None
        if ( arguments['-e'] ):
            stopdir = utils.standardize_dir_sep( arguments['-e'] )
            
            # Trap special case of using 'xpkgs' directory
            if ( stopdir.startswith(NQBP_WRKPKGS_DIRNAME()) ):
                stopdir = os.sep + stopdir[len(NQBP_WRKPKGS_DIRNAME())+1:]
        
        # Build all directories    
        for d in libdirs:
            skip, stop = build_single_directory( arguments, toolchain, d[0], d[1], skip, startdir, stop, stopdir )
    
    # Build project dir
    if ( bld_prj and not stop ):
        # Banner 
        utils.output( "=====================" )
        utils.output( "= Building Project Directory:" )
    
        # check for existing 'sources.b' file 
        files = utils.get_files_to_build( toolchain, '.', NQBP_NAME_SOURCES() )

        # compile files
        for f in files:
            toolchain.cc( arguments, '.' + os.sep + f )
    
    # Peform link
    if ( do_link ):
        inf = open( NQBP_NAME_LIBDIRS(), 'r' )
        toolchain.link( arguments, inf, 'local', variant )
        inf.close()
                            
    # Output end banner
    end_banner(toolchain)
     
           
#-----------------------------------------------------------------------------
def pre_build_steps(toolchain, arguments ):

    # Enable only 'normal' outputs
    utils.enable_ouptut()
    
    # Enable verbose logging (if selected)
    if ( arguments['-v'] ):
        utils.enable_verbose()
    
    # Enable debugging logging (if selected) note: order is important here -->must follow enable.verbose()    
    if ( arguments['--debug'] ):
        utils.enable_debug()
        
        
            
#-----------------------------------------------------------------------------
def start_banner(toolchain):

    # 
    start = int( toolchain.get_build_time() ) 
    utils.output('')
    utils.output( '=' * 80 );
    utils.output( '= START of build for:  %s', toolchain.get_final_output_name() )
    utils.output( '= Toolchain:           %s', toolchain.get_ccname() )
    utils.output( '= Build Configuration: %s', toolchain.get_build_variant() )
    utils.output( '= Begin (UTC):         %s', time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) )
    utils.output( '= Build Time:          %d (%X)', start, start )
    utils.output( '=' * 80 );

        
#-----------------------------------------------------------------------------
def end_banner(toolchain):

    # Calculate elasped time in hhh mm ss    
    elasped = int(time.time() - toolchain.get_build_time()) 
    mm      = (elasped // 60) % 60
    hhh     = elasped // (60*60)
    ss      = elasped % 60
    
    # 
    utils.output( '=' * 80 );
    utils.output( '= END of build for:    %s', toolchain.get_final_output_name() )
    utils.output( '= Toolchain:           %s', toolchain.get_ccname() )
    utils.output( '= Build Configuration: %s', toolchain.get_build_variant() )
    utils.output( '= Elapsed Time (hh mm:ss): {:02d} {:02d}:{:02d}'.format(hhh, mm, ss) )
    utils.output( '=' * 80 );

    
#-----------------------------------------------------------------------------
def build_single_file( arguments, toolchain ):

    # Get file to compile
    is_project_dir = False
    fname          = utils.standardize_dir_sep( arguments['-f'] )
    srcpath        = NQBP_PKG_ROOT() + os.sep
    
    # Trap that file is relative to package root
    if ( fname.startswith(os.sep) ):
        fname   = fname[1:]
        srcpath = NQBP_PKG_ROOT() + os.sep
            
    # Trap that file is relative to workspace root
    elif ( fname.startswith(os.sep+os.sep) ):
        fname   = fname[2:]
        srcpath = NQBP_WORK_ROOT() + os.sep
            
    # Trap that file is relative to the build directory
    elif ( fname.startswith('.') ):
        srcpath        = os.getcwd() + os.sep
        is_project_dir = True
        
    # create object directory 
    if ( is_project_dir ):
        dir = os.getcwd()
    else:
        dir = utils.create_subdirectory_from_file( os.getcwd(), fname )
    
    # call toolchain compile method
    utils.push_dir( dir )
    toolchain.cc( arguments, srcpath + fname )

    # build archive (when not compiling a file in the project directory)
    if ( not is_project_dir ):
        toolchain.ar( arguments )
    utils.pop_dir()
    
#-----------------------------------------------------------------------------
def build_single_directory( arguments, toolchain, dir, entry, skip=False, startdir=None, stop=False, stopdir=None ):
   
    srcpath = ''
    display = ''
    
    # directory is local to my package
    if ( entry == 'local' ):
        srcpath = NQBP_PKG_ROOT() + os.sep + dir
        display = dir
    
    elif ( entry == 'pkg' ):
        srcpath = os.path.join( NQBP_PKG_ROOT(), dir )
        display = dir
        
    # directory is an external package
    else:
        display = os.sep + dir
        srcpath = NQBP_WORK_ROOT() + os.sep + NQBP_WRKPKGS_DIRNAME() + os.sep + dir
        dir     = NQBP_WRKPKGS_DIRNAME() + os.sep + dir

    # Handle the skip option
    if ( skip ):
        # match start directory
        if ( startdir != display ):
            utils.output( "= Skippping directory: " + display )
            return True, stop
        else:
            skip = False

    # Handle the stop option
    if ( stopdir != None ):
        # indicate that directories are being skipped
        if ( stop ):
            utils.output( "= Skippping directory: " + display )
            return skip, stop
            
        # match stop directory
        if ( stopdir == display ):
            stop = True
        
        
    # Banner 
    utils.output( "=====================" )
    utils.output( "= Building Directory: " + display )

    # Debug info
    utils.debug( "#   entry  = {}".format( entry ) )
    utils.debug( "#   objdir = {}".format( dir ) )
    utils.debug( "#   srcdir = {}".format( srcpath ) )

    
    # verify source directory exists
    if ( not os.path.exists( srcpath ) ):
        utils.output( "")
        utils.output( "ERROR: Build Failed - directory does not exist: " )
        utils.output( "" )
        sys.exit(1)
        
    # create object directory 
    dir = utils.create_subdirectory( os.getcwd(), dir )
    utils.push_dir( dir )

    # check for existing 'sources.b' file 
    files = utils.get_files_to_build( toolchain, srcpath, NQBP_NAME_SOURCES() )

    # compile files
    for f in files:
        toolchain.cc( arguments, srcpath + os.sep + f )
        
    # build archive
    toolchain.ar( arguments )
    utils.pop_dir()

    # return skip/stop status
    return skip, stop