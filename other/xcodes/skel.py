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
    -n NAMESPACE        Explicity provide the namespace. Format: "N1::N2::N3.."
                        The default operation is to derive the namespace(s) from
                        the current working directory.
    -h, --help          Display help for this command

Common Options:
    See 'xcode --help'


Notes:
        
"""
from nqbplib.docopt.docopt import docopt
from nqbplib import utils
from other import utils2
import os, sys

# globals
WRKSPACE_ROOT = ''
PKG_ROOT      = ''

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print "{:<13}{}".format( 'skel', 'Generate skeleton C++ header/cpp files' )
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    global WRKSPACE_ROOT
    global PKG_ROOT
    
    # Parse command line
    args = docopt(__doc__, argv=cmd_argv)
    
    # Get workspace/package info
    WRKSPACE_ROOT, PKG_ROOT = utils2.set_pkg_and_wrkspace_roots()
    
    # Get namespace as a list
    if ( args['-n'] ):
        namespaces = args['-n'].split('::')
    else:
        namespaces = utils2.get_relative_subtree( PKG_ROOT, 'src' ).split( os.sep )
    names = ','.join( namespaces )
    
    # Generate header file
    if ( not args['--cpp'] ):
        ofname     = args['<class>']+".h"
        cmd        = 'f4 header_skeleton.f4t -z --global //colony.core/resources/f4 -v {} -o {} map "{}" {} {}'.format( common_args['-g'], ofname, common_args['-c'], args['<class>'], names )
        rc, output = utils2.run_shell( cmd )
        verbose( cmd, output, common_args )
        if ( rc != 0 ):
            sys.exit( "ERROR: Failed to create output: {}.  Rerun using the '-v' for additional error information".format(ofname) )
        
    # Generate CPP file
    if ( not args['--header'] ):
        ofname     = args['<class>']+".cpp"
        cmd        = 'f4 cpp_skeleton.f4t -z --global //colony.core/resources/f4 -v {} -o {} map "{}" {} {}'.format( common_args['-g'], ofname, common_args['-c'], args['<class>'], names )
        rc, output = utils2.run_shell( cmd )
        verbose( cmd, output, common_args )
        if ( rc != 0 ):
            sys.exit( "ERROR: Failed to create output: {}.  Rerun using the '-v' for additional error information".format(ofname)  )
    
#------------------------------------------------------------------------------
###
def verbose( cmd, output, args ):
    if ( args['-v'] ):
        print cmd
        utils2.print_shell_output( output )
    
