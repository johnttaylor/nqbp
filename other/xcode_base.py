#!/usr/bin/env python
"""
 
Xcode generates source code template/skeleton files
===============================================================================
usage: xcode [options] <template> [<args>...]
       xcode [options]

Options:
    -c COPYRIGHT        Overrides the default copy right holder
    -v                  Be verbose. 
    -g                  Enable debug switch on the 'f4' utility
    -h, --help          Display help for common options/usage.
    

Type 'xcode help <template>' for help on a specific template.

"""

import sys
import os
from subprocess import call

from nqbplib.docopt.docopt import docopt
from nqbplib import utils




#------------------------------------------------------------------------------
def load_command( name ):
        try:
            command_module = __import__("other.xcodes.{}".format(name), fromlist=["other.xcodes"])
        except ImportError:
            exit("{} is not a xcode template. Use 'xcode help' for list of templates.".format(name) )

        return command_module
        
        
#------------------------------------------------------------------------------
def display_command_list():
    import pkgutil
    import xcodes
    p = xcodes
    
    print( ' ' )
    print( "Type 'xcode help <template>' for more details. Type 'xcode -h' for base usage." )
    print( "-------------------------------------------------------------------------------" )
    
    for importer, modname, ispkg in pkgutil.iter_modules(p.__path__):
        if ( not ispkg ):
            cmd = load_command( modname )
            cmd.display_summary()
            

    print( ' ' )

#------------------------------------------------------------------------------
def run( argv ):

    # Parse command line
    args = docopt(__doc__, version="0.1", options_first=True )

    # Trap help on a specific command
    if ( args['<template>'] == 'help' ):

        # Display list of commands if none specified
        if ( args['<args>'] == [] ):
            display_command_list()
        
        # Display command specific help
        else:
            load_command( args['<args>'][0] ).run( args, ['--help'] )


    # Trap no command specified        
    elif ( args['<template>'] == None ):
            docopt(__doc__,argv=['--help'])
    

    # Run the command (if it exists)
    else:
        # Set the default copyright holder
        if ( not args['-c'] ):
            args['-c'] = "John T. Taylor"
       
        # Convert the debug option to a f4 argument
        if ( args['-g'] ):
            args['-g'] = '-g'
        else:
            args['-g'] = ''
             
        # run the command
        load_command( args['<template>'] ).run( args, [args['<template>']] + args['<args>'] )


    

