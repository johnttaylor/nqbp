"""Collection of helper functions"""

import os
import logging
import sys
import subprocess

# Globals
from my_globals import NQBP_WORK_ROOT
from my_globals import NQBP_PKG_ROOT
from my_globals import NQBP_TEMP_EXT
from my_globals import NQBP_VERSION
from my_globals import NQBP_PRJ_DIR
from my_globals import NQBP_NAME_LIBDIRS
from my_globals import NQBP_PRJ_DIR_MARKER1
from my_globals import NQBP_PRJ_DIR_MARKER2
from my_globals import NQBP_PKG_TOP
from my_globals import NQBP_WRKPKGS_DIRNAME


# Module globals
_dirstack = []


# Get logger/output handle
OUT = logging.getLogger( 'nqbp' )


#-----------------------------------------------------------------------------
def dir_list_filter_by_ext(dir, exts): 
    """Returns a list of files filter by the passed file extensions
    
    Accepts one or more file extensions (with no '.') 
    """
    
    results = []
    for name in os.listdir(dir):
        for e in exts:
            if ( name.endswith("." + e) ):
                results.append(name)

    return results


#-----------------------------------------------------------------------------
def run_shell( cmd, capture_output=True ):
    p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    r = p.communicate()

    if ( r[0] != None ):
        line =  r[0].rstrip()
        if ( line != "" ):
            output( line )
            
    if ( r[1] != None ):
        line =  r[1].rstrip()
        if ( line != "" ):
            output( line )

    return p.returncode


#-----------------------------------------------------------------------------
def del_files_by_ext(dir, *exts): 
    """Delete file(s) from 'dir' based the passed file extensions
    
    Accepts one or more file extensions (with no '.') 
    """

    files_to_delete = dir_list_filter_by_ext( dir, *exts )
    for f in files_to_delete:
        os.remove(f)

def output(*args):
    OUT.warning( *args )
    
def verbose(*args):
    OUT.info( *args )
    
def debug(*args):
    OUT.debug( *args )
    
def enable_debug():
    OUT.setLevel( logging.DEBUG )
    
def enable_verbose():
    OUT.setLevel( logging.INFO )
    
def enable_ouptut():
    # Setup logger to echo output to console and log file
    OUT.setLevel( logging.WARNING )
    fh = logging.FileHandler( 'make.log', 'w' )
    fh.setLevel(logging.DEBUG )
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG )
    formatter = logging.Formatter( '%(message)s' )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    OUT.addHandler(fh)
    OUT.addHandler(ch)
    
def remove_log_file():
    # Brute force close all logger handlers so I can delete the 'file logger'
    for h in OUT.handlers:
        OUT.removeHandler(h)
        h.close()
        
    delete_file('make.log')
    
    
#-----------------------------------------------------------------------------
def create_working_libdirs( inf, arguments, libdirs, local_external_flag, variant, parent=None ):
    
    # process all entries in the file        
    for line in inf:
        # 'normalize' the file entries
        line      = standardize_dir_sep( line.strip() )
        entry     = local_external_flag
        newparent = parent
        
        # drop comments and blank lines
        if ( line.startswith('#') ):
            continue
        if ( line == '' ):
            continue
        
        # Filter by variant
        if ( line.startswith('[') ):
            tokens = line[1:].split(']')
            if ( len(tokens) == 1 ):
                output( "ERROR: invalid [<variant>] prefix qualifer ({})".format( line ) )
                sys.exit(1)
            if ( not _matches_variant(tokens[0], variant) ):
                continue

            # Remove the filter prefix
            line = line.split(']')[1].strip()
            
            
        # Calc root/leading path    
        if ( line.startswith(os.sep+os.sep) ):
            path      = os.path.join(NQBP_WORK_ROOT(), NQBP_WRKPKGS_DIRNAME() ) + os.sep
            line      = line [2:]
            entry     = 'xpkg'
            newparent = line.split(os.sep)[0]
     
            # Skip external dirs when requested
            if ( arguments['-p'] ):
                continue
                    
        elif ( line.startswith('.') ):
            
            # all relative includes must be libdirs.b includes
            if ( not line.endswith( NQBP_NAME_LIBDIRS() ) ):
                output( "ERROR: using a relative include to a non-libdirs.b file ({})".format( line ) )
                sys.exit(1)
                
            path  = NQBP_PRJ_DIR() + os.sep
            
            
        else:
            # Skip local/package dirs when requested to only build external directories
            if ( arguments['-x'] ):
                continue
                
            if ( line.startswith(os.sep) ):
                path    = NQBP_PKG_ROOT() + os.sep
                line    = line [1:]
                entry   = 'pkg'
               
            # append 'parent' when there is one, i.e. when I have been include from xpkg libdirs.b    
            else:
	        if ( newparent != None ):
		    line = os.path.join(newparent,line)
            
            
        # trap nested 'libdirs.b' files
        if ( line.endswith( NQBP_NAME_LIBDIRS() ) ):
            fname = path+line
            if ( not os.path.isfile(fname) ):
                output( "ERROR: Missing/invalid nest '{}': {}".format(NQBP_NAME_LIBDIRS(),line) )
                sys.exit(1)
                
            f = open( path+line, 'r' )
            create_working_libdirs( f, arguments, libdirs, entry, variant, newparent )
            f.close()
            continue               

        # output the line
        libdirs.append( (line, entry) )
        
     
#-----------------------------------------------------------------------------
def create_subdirectory( pardir, new_subdir ):
    dname  = os.path.abspath( standardize_dir_sep(pardir) + os.sep + new_subdir )
    
    try:
        os.makedirs(dname)
        
    except OSError:
        if ( os.path.exists(dname) ):
            # Directory already exists -->no actual error
            pass
            
        else:
            output( "ERROR: Failed to create directory: {}".format( dname ) )
            sys.exit(1)
            
    return dname
    
    
def create_subdirectory_from_file( pardir, fname ):
    subdir = os.path.dirname( standardize_dir_sep(fname) )
    dname  = os.path.abspath( standardize_dir_sep(pardir) + os.sep + subdir )
    
    try:
        os.makedirs(dname)
        
    except OSError:
        if ( os.path.exists(dname) ):
            # Directory already exists -->no actual error
            pass
            
        else:
            output( "ERROR: Failed to create directory: {}".format( dname ) )
            sys.exit(1)
            
    return dname
    
        
#-----------------------------------------------------------------------------
def set_pkg_and_wrkspace_roots(from_fname):
    from_fname = os.path.abspath(from_fname)
    root = _get_marker_dir( standardize_dir_sep(from_fname), NQBP_PRJ_DIR_MARKER1() )
    if ( root != None ):
        pass
    
    else:
        root = _get_marker_dir( standardize_dir_sep(from_fname), NQBP_PRJ_DIR_MARKER2() )
        if ( root != None ):
            pass
            
        else:
            print( "ERROR: Cannot find the 'Package Root'" )
            sys.exit(1)
                
    NQBP_WORK_ROOT( os.path.dirname(root) )     
    NQBP_PKG_ROOT( root )
    
   
def _get_marker_dir( from_fname, marker ):
    path   = from_fname.split(os.sep)
    result = ''  
    idx    = 0  
    path.reverse()
    
    try:
        idx = path.index(marker)
        idx = len(path) - idx -1
        path.reverse()
        for d in path[1:idx]:
            result += os.sep + d
        
    except:
        result = None
    
    if ( result != None ):
        result = _test_for_top( result, marker )    
    return result
    

def _test_for_top( dir, marker ):
    while( dir != None ):
        if ( os.path.isdir(dir + os.sep + NQBP_PKG_TOP()) ) :
            break
        else:
            dir = _get_marker_dir( dir, marker )
    
    return dir
    
    
def _matches_variant( filter, my_variant ):
    tokens = filter.split('|')
    for t in tokens:
        if ( t.strip() == my_variant ):
            return True
    return False    
                    
#--------------------------------------------------------------------------
def delete_file( fname ):
    """ remove file(s) and suppress error if 'fname' does not exist """
    
    result = False
    try:
        os.remove( fname )
        result = True
    except OSError:
        pass
           
    return result
    
           
#-----------------------------------------------------------------------------
def standardize_dir_sep( pathinfo ):
    return pathinfo.replace( '/', os.sep ).replace( '\\', os.sep )

def push_dir( newDir ):
    global _dirstack
    _dirstack.append( os.getcwd() )
    os.chdir( newDir )
    
    
def pop_dir():
    global _dirstack
    os.chdir( _dirstack.pop() )
    
    
#-----------------------------------------------------------------------------
def get_files_to_build( toolchain, dir, sources_b ):
    files = []
    
    # get the list of potential file to build (when no 'sources.b' is present)
    if ( not os.path.isfile( sources_b) ):
        files = dir_list_filter_by_ext(dir, ['c', 'cpp'] + toolchain.get_asm_extensions() )
        debug( "# Creating auto.sources.b for dir: {}".format( dir ) )
                
    # get the list of files to build from 'sources.b'
    else:
        inf = open( sources_b, 'r' )
        for line in inf:
            # drop comments and blank lines
            line = line.strip() 
            if ( line.startswith('#') ):
                continue
            if ( line == '' ):
                continue
            
            files.append( line )
       
        inf.close()
             
    # return the file list
    return files                
    
#-----------------------------------------------------------------------------
def list_libdirs( libs ):
    debug( "# Expanded libdirs.b: (localFlag, srcdir)" )
    for l in libs:
        dir,flag = l
        debug( "#   {:<5}:  {}".format( str(flag), dir)  )
