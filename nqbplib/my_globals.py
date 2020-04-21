#!/usr/bin/python3
""" Global variables """

import os
import logging
    
# Globals
_NQBP_WORK_ROOT               = ''
_NQBP_PRJ_DIR                 = ''
_NQBP_PKG_ROOT                = ''
_NQBP_PRE_PROCESS_SCRIPT      = None
_NQBP_PRE_PROCESS_SCRIPT_ARGS = ''
_NQBP_INITIAL_LIBDIRS         = []
_NQBP_OUTCAST_MODE            = None

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
    if NQBP_OUTCAST_MODE():
        return 'xpkgs' 
    else:
        return 'xsrc' 

            
def NQBP_PUBLICAPI_DIRNAME():
    if NQBP_OUTCAST_MODE():
        return NQBP_WORK_ROOT() + os.sep + 'xinc' + os.sep + 'src'
    else:
        return NQBP_PKG_ROOT() + os.sep + 'xsrc'
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
          
#
def NQBP_PRE_PROCESS_SCRIPT( newval=None ):
    global _NQBP_PRE_PROCESS_SCRIPT
    if ( newval != None ):
        _NQBP_PRE_PROCESS_SCRIPT = newval
    return _NQBP_PRE_PROCESS_SCRIPT          
    
#
def NQBP_PRE_PROCESS_SCRIPT_ARGS( newval=None ):
    global _NQBP_PRE_PROCESS_SCRIPT_ARGS
    if ( newval != None ):
        _NQBP_PRE_PROCESS_SCRIPT_ARGS = newval
    return _NQBP_PRE_PROCESS_SCRIPT_ARGS   


#
def NQBP_OUTCAST_MODE():
    global _NQBP_OUTCAST_MODE
    if ( _NQBP_OUTCAST_MODE == None ):
        val = os.environ.get('NQBP_OUTCAST_MODE')
        if ( val == None or val != 'true' ):
            _NQBP_OUTCAST_MODE = False;
        else:
            _NQBP_OUTCAST_MODE = True;

    return _NQBP_OUTCAST_MODE
    
    
