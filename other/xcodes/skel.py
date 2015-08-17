"""
 
Generates skeleton C++ header/cpp files
===============================================================================
usage: xcode [common-opts] skel [options] <class>


Arguments:
    <class>         Class/File name with NO file extension.  This argument IS
                    case sensistive.
                        
Options:
    --header            Only generates a header file
    --cpp               Only generates a CPP file
    --no-auto-ns        Do not derive the namespace from the current directory
    -n NAMESPACE        Explicity provide the namespace
    -h, --help          Display help for this command

Common Options:
    See 'xcode --help'


Notes:
        
"""
from nqbplib.docopt.docopt import docopt
from nqbplib import utils
from other import utils2
import os

# globals
WRKSPACE_ROOT = ''
PKG_ROOT      = ''

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print "{:<13}{}".format( 'skel', 'Generate skeleton C++ header/cpp files' )
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    global WRKSPACE_ROOT
    global PKG_ROOT
    WRKSPACE_ROOT, PKG_ROOT = utils2.set_pkg_and_wrkspace_roots()
    print WRKSPACE_ROOT, PKG_ROOT
    
#------------------------------------------------------------------------------
        
