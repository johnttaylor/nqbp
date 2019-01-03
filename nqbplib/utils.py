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
from my_globals import OUT

# Module globals
_dirstack = []


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


def source_list_to_object_list( root_dir, src_dir, exts, obj_extension, new_root ):
    """ Converts a source directory into a list of object files AND replaces
        the source's 'root_dir' in the path with 'new_root'.  The list is returned
        as single string.

        NOTE: This function is workaround because of how the Windows CMD shell
              does NOT expand wildcards (i.e. can't pass *.obj to the mingw
              gcc compiler and have if work as expected)
    """

    files = dir_list_filter_by_ext( os.path.join(root_dir,src_dir), exts )

    objs  = '';
    for f in files:
        basename = os.path.splitext(f)[0]
        basename = os.path.join(new_root, src_dir, basename)
        objs = objs + ' ' + basename + '.' + obj_extension

    return objs

#-----------------------------------------------------------------------------
def run_shell( printer, cmd, capture_output=True ):
    p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE ) if capture_output else subprocess.Popen( cmd, shell=True ) 
    r = p.communicate()

    if ( r[0] != None ):
        line =  r[0].rstrip()
        if ( line != "" ):
            printer.output( line )
            
    if ( r[1] != None ):
        line =  r[1].rstrip()
        if ( line != "" ):
            printer.output( line )

    return p.returncode


#-----------------------------------------------------------------------------
def del_files_by_ext(dir, *exts): 
    """Delete file(s) from 'dir' based the passed file extensions
    
    Accepts one or more file extensions (with no '.') 
    """

    files_to_delete = dir_list_filter_by_ext( dir, *exts )
    for f in files_to_delete:
        os.remove(f)

    
#-----------------------------------------------------------------------------
def expand_environ_var_dir_path( printer, dir_path, marker='$' ):
    envvar, subpath = dir_path[1:].split(marker, 1)
    rootpath = os.environ.get(envvar)
    if ( rootpath == None ):
        printer.output( "ERROR: Non-existent environment variable - {} - reference in line ({})".format(envvar,dir_path))
        sys.exit(1)
    subpath = subpath.lstrip(os.sep)
    return os.path.join(rootpath, subpath)
    

#-----------------------------------------------------------------------------
def replace_environ_variable( printer, line, marker='$' ):
    # Find the next environment variable
    start_idx = line.find(marker)
    if ( start_idx < 0 ):
        return line
    end_idx = line.find(marker,start_idx+1)
    if ( end_idx < 0 ):
        printer.output( "ERROR: Invalid variable syntax - missing trailing {} - in line:({})".format(marker,line) )
        sys.exit(1)

    # Expand the environment variable's content
    var   = line[start_idx+1:end_idx]
    value = os.environ.get(var)
    if ( value == None ):
        printer.output( "ERROR: Non-existent environment variable - {} - reference in line ({})".format(var,line))
        sys.exit(1)
    line = line[:start_idx] + value + line[end_idx+1:]

    # Keeping search for other environment variables....
    return replace_environ_variable(printer,line,marker)

#-----------------------------------------------------------------------------
def create_working_libdirs( printer, inf, arguments, libdirs, local_external_flag, variant, parent=None ):
    
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
                printer.output( "ERROR: invalid [<variant>] prefix qualifer ({})".format( line ) )
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
     
        # Absolute root path via an environment variable
        elif ( line.startswith('$')):
            line = replace_environ_variable( printer, line )
            entry = 'absolute'

        # relative path (i.e. an '#include' statement)
        elif ( line.startswith('.') ):
            
            # all relative includes must be libdirs.b includes
            if ( not line.endswith( NQBP_NAME_LIBDIRS() ) ):
                printer.output( "ERROR: using a relative include to a non-libdirs.b file ({})".format( line ) )
                sys.exit(1)
                
            path  = NQBP_PRJ_DIR() + os.sep
            
            
        # within my package...
        else:
            if ( line.startswith(os.sep) ):
                path    = NQBP_PKG_ROOT() + os.sep
                line    = line [1:]
                entry   = 'pkg'
               
            # append 'parent' when there is one, i.e. when I have been include from xpkg libdirs.b    
            else:
                if ( newparent != None ):
                    line = os.path.join(newparent,line)
            
            
        # Expand any/all embedded environments variables (that did NOT start the directory entry)
        line = replace_environ_variable(printer, line)

        # trap nested 'libdirs.b' files
        if ( line.endswith( NQBP_NAME_LIBDIRS() ) ):
            fname = path+line
            if ( not os.path.isfile(fname) ):
                printer.output( "ERROR: Missing/invalid nest '{}': {}".format(NQBP_NAME_LIBDIRS(),line) )
                sys.exit(1)
                
            f = open( path+line, 'r' )
            create_working_libdirs( printer, f, arguments, libdirs, entry, variant, newparent )
            f.close()
            continue               

        # output the line
        if ( arguments['-p'] and entry == 'xpkg' ):
            pass
        elif ( arguments['-x'] and entry != 'xpkg' ):
            pass
        elif ( arguments['--noabs'] and entry == 'absolute' ):
            pass
        else:
            libdirs.append( (line, entry) )
        
     
#-----------------------------------------------------------------------------
def create_subdirectory( printer, pardir, new_subdir ):
    dname  = os.path.abspath( standardize_dir_sep(pardir) + os.sep + new_subdir )
    
    try:
        os.makedirs(dname)
        
    except OSError:
        if ( os.path.exists(dname) ):
            # Directory already exists -->no actual error
            pass
            
        else:
            printer.output( "ERROR: Failed to create directory: {}".format( dname ) )
            sys.exit(1)
            
    return dname
    
    
def create_subdirectory_from_file( printer, pardir, fname ):
    subdir = os.path.dirname( standardize_dir_sep(fname) )
    dname  = os.path.abspath( standardize_dir_sep(pardir) + os.sep + subdir )
    
    try:
        os.makedirs(dname)
        
    except OSError:
        if ( os.path.exists(dname) ):
            # Directory already exists -->no actual error
            pass
            
        else:
            printer.output( "ERROR: Failed to create directory: {}".format( dname ) )
            sys.exit(1)
            
    return dname
    
        
#-----------------------------------------------------------------------------
def set_pkg_and_wrkspace_roots( from_fname):
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
    
    if ( result == None ):
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
def get_files_to_build( printer, toolchain, dir, sources_b ):
    files = []
    
    # get the list of potential file to build (when no 'sources.b' is present)
    src_b = os.path.join( dir, sources_b )
    if ( not os.path.isfile( src_b) ):
        exts = ['c', 'cpp'] + toolchain.get_asm_extensions()
        printer.debug( "# Creating auto.sources.b for dir: {}. Extensions={}".format( dir, exts )  )
        files = dir_list_filter_by_ext(dir, exts )
                
    # get the list of files to build from 'sources.b'
    else:
        inf = open( src_b, 'r' )
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
def list_libdirs( printer, libs ):
    printer.debug( "# Expanded libdirs.b: (localFlag, srcdir)" )
    for l in libs:
        dir,flag = l
        printer.debug( "#   {:<5}:  {}".format( str(flag), dir)  )
