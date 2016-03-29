""" Global variables """

import os
import logging
    
# Globals
_NQBP_WORK_ROOT = ''
_NQBP_PRJ_DIR   = ''
_NQBP_PKG_ROOT  = ''

# Initialize globals
OUT = logging.getLogger( 'nqbp' )

#
def NQBP_VERSION():
    return "v0.0.5"
    
#
def NQBP_TEMP_EXT():
    return '_temp_nqbp'

#
def NQBP_NAME_LIBDIRS():
    return 'libdirs.b'

#
def NQBP_NAME_SOURCES():
    return 'sources.b'

def NQBP_WRKPKGS_DIRNAME():
    return 'xpkgs' 
            
def NQBP_PUBLICAPI_DIRNAME():
    return 'xinc' 
            
#
def NQBP_PKG_TOP():
    return 'top'
    
#
def NQBP_PRJ_DIR_MARKER1():    
    return "projects"
    
#
def NQBP_PRJ_DIR_MARKER2():    
    return "tests"

  
#
def NQBP_PRJ_DIR( newval=None ):
    global _NQBP_PRJ_DIR
    if ( newval != None ):
        if ( newval.endswith(os.sep) ):
            newval [:-1]
        _NQBP_PRJ_DIR = newval
    return _NQBP_PRJ_DIR

#
def NQBP_WORK_ROOT( newval=None ):
    global _NQBP_WORK_ROOT
    if ( newval != None ):
        if ( newval.endswith(os.sep) ):
            newval [:-1]
        _NQBP_WORK_ROOT = newval
    return _NQBP_WORK_ROOT
    
#
def NQBP_PKG_ROOT( newval=None ):
    global _NQBP_PKG_ROOT
    if ( newval != None ):
        if ( newval.endswith(os.sep) ):
            newval [:-1]
        _NQBP_PKG_ROOT = newval
    return _NQBP_PKG_ROOT
          
    
    
    
    
