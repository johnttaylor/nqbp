#!/usr/bin/env python
#=============================================================================
# Helper script (that does most of work) for generating FSM source code from
# Cadifra FSM diagrams
#
# This script runs the 'sinelaboreRT' Finite State Machine Code Generator
# utility.  The SinelaboreRT tool is proprietary tool, but the output of
# the code generator is NOT.  This script is also specific to parsing
# FSM diagramS generated by the Cadifra drawing tool (yet another 
# proprietary tool).  Yes - using non open source tools is straying from
# the pure faith - but both tools are very good and affordable - and the
# generated source code and diagram content is still 'free'.
#
# http://www.sinelabore.com/
# http://www.cadifra.com/
#
#=============================================================================

#
import sys   
import os
import subprocess
#
from nqbplib.docopt.docopt import docopt
from nqbplib import utils


# 
usage = """ 
genfsm - Generates source code from Cadifra FSM Diagrams (.cdd files)
===============================================================================
Usage: genfsm [options] <basename> <namespaces>

Arguments:
  <basename>       Base name for the FSM.  The Cadifra diagram must have this
                   same file name.  All generated output files will have the 
                   <basename> as part of their file names. <basename> IS 
                   case sensitive!
      
  <namespaces>     The encapsulated namespace(s) for the generated files. The
                   Format is: 'Rte::Db::Record'
                   
Options:
  -h, --help       Display command help.
        
         
NOTES:
    o The environment variable SINELABORE_PATH is required/used to specify
      the location of the Sinelabore code generator JAR files (and it 
      supporting JAR files).
    o The script assumes that Graphviz's dot.exe is in the command path.
      GraphViz is used to generated the FSM diagram for Doxygen. See 
      http://www.graphviz.org
      
"""

#
import subprocess
import re
import sys

#------------------------------------------------------------------------------
# Parse command line
def run( argv ):

    print argv
    
    # Process command line args...
    args = docopt(usage, version="0.0.1" )
    
    # Check the environment variables 
    sinpath = os.environ.get( "SINELABORE_PATH" )
    if ( sinpath == None ):
        exit( "ERROR: The SINELABORE_PATH environment variable is not set." )
    
    # Convert namespace arg to list
    names = args['<namespaces>'].split('::')
    
    # Filenames
    fsmdiag = args['<basename>'] + ".cdd"
    base    = args['<basename>'] + "Context_" 
    fsm     = args['<basename>'] 
    cfg     = 'codegen.cfg'
      
    # Create the config file for Sinelabore
    geneatedCodegenConfig( cfg, base, names )
        
    # Build Sinelabore command
    cmd = 'java -jar -Djava.ext.dirs={} {}/codegen.jar -p CADIFRA -doxygen -o {} -l cppx -Trace {}'.format( sinpath, sinpath, fsm, fsmdiag )
    cmd = utils.standardize_dir_sep( cmd )
  
    # Invoke Sinelabore command
    print cmd
    p = subprocess.Popen( cmd, shell=True )
    r = p.communicate()
    if ( p.returncode != 0 ):
        exit("ERROR: Sinelabore encounterd an error or failed to run." )
    
    # Clean-up config file (don't want it being checked into version control)
    os.remove( cfg )
    
    # Generate Context/Base class
    actions, guards = getContextMethods( fsmdiag )
    generatedContextClass( base, names, getHeader(), actions, guards )
    
    # Post process the generated file(s) to work better with Doxygen
    cleanup_for_doxygen( fsm + ".h", args['<namespaces>'] + "::" + fsm )
      
    # Generated File names
    oldfsm    = fsm + '.h'
    oldfsmcpp = fsm + '.cpp'
    oldevt    = fsm + '_ext.h'
    oldtrace  = fsm + '_trace.h'
    oldtrace2 = fsm + '_trace.java'
    newfsm    = fsm + '_.h'
    newfsmcpp = fsm + '_.cpp'
    newevt    = fsm + '_ext_.h'
    newtrace  = fsm + '_trace_.h'
    
    # Post process the generated file(s) 
    cleanup_trace( oldfsmcpp, names, fsm, oldfsm, oldtrace, newtrace )
    cleanup_includes( oldfsm,    names, oldfsm, newfsm, oldevt, newevt, base + '.h' )
    cleanup_includes( oldfsmcpp, names, oldfsm, newfsm, oldevt, newevt, base + '.h' )
      
    # Housekeeping for naming convention
    utils.delete_file( newfsm )
    utils.delete_file( newfsmcpp )
    utils.delete_file( newevt )
    utils.delete_file( newtrace )
    utils.delete_file( oldtrace2 )  # remove unwanted JAVA file
    os.rename( oldfsm, newfsm )
    os.rename( oldfsmcpp, newfsmcpp ) 
    os.rename( oldevt, newevt ) 
    os.rename( oldtrace, newtrace ) 



#------------------------------------------------------------------------------
def cleanup_for_doxygen( headerfile, classname ):
    tmpfile = headerfile + ".tmp"
    with open( headerfile ) as inf:
        with open( tmpfile, "w") as outf:  
            for line in inf:
                if ( line.find( 'Here is the graph that shows the state machine' ) == -1 ):
                    outf.write( line )
                else:
                    outf.write( "/** \class {}\nHere is the graph that shows the state machine this class implements\n\dot\n".format( classname ) )
    
    os.remove( headerfile )
    os.rename( tmpfile, headerfile )
                     

def cleanup_includes( headerfile, namespaces, oldfsm, newfsm, oldevt, newevt, base ):
    tmpfile = headerfile + ".tmp"
    path    = path_namespaces( namespaces )
    
    with open( headerfile ) as inf:
        with open( tmpfile, "w") as outf:  
            for line in inf:
                if ( line.find( '#include "{}"'.format(oldfsm) ) != -1):
                    outf.write( '#include "{}{}"\n'.format(path, newfsm) )
                elif ( line.find( '#include "{}"'.format(oldevt) ) != -1) :
                    outf.write( '#include "{}{}"\n'.format(path, newevt) )
                elif ( line.find( '#include "{}"'.format(base) ) != -1) :
                    outf.write( '#include "{}{}"\n'.format(path, base) )
                else:
                    outf.write( line )
    
    os.remove( headerfile )
    os.rename( tmpfile, headerfile )
      
      
def cleanup_trace( cppfile, namespaces, base, oldfsm, old_trace_headerfile, new_trace_headerfile ):
    # Add xx_trace_.h include to xxx_.cpp
    tmpfile  = cppfile + ".tmp"
    path     = path_namespaces( namespaces )
    newstate = 'stateVars = stateVarsCopy;'
    
    with open( cppfile ) as inf:
        with open( tmpfile, "w") as outf:  
            for line in inf:
                outf.write( line )
                if ( line.find( '#include "{}"'.format(oldfsm) ) != -1):
                    outf.write( '#include "{}{}"\n'.format(path, new_trace_headerfile) )
                elif ( line.find( newstate ) != -1 ):
                    outf.write( '    CPL_SYSTEM_TRACE_MSG( SECT_, ( "New State=%s", getNameByState(getInnermostActiveState()) ));\n' )
    
    os.remove( cppfile )
    os.rename( tmpfile, cppfile )

    # add CPL trace hooks
    tmpfile  = old_trace_headerfile + ".tmp"
    path     = path_namespaces( namespaces )
    trace_fn = 'TraceEvent(int evt);'
    enum     = 'enum ' + base + 'TraceEvent'
    comment  = '/* Simulation which'
    
    with open( old_trace_headerfile ) as inf:
        with open( tmpfile, "w") as outf:  
            for line in inf:
                if ( line.find( '#define' ) != -1):
                    outf.write( line )
                    outf.write( '\n' )
                    outf.write( '#include "Cpl/System/Trace.h"\n' )
                    outf.write( '\n' )
                    outf.write( '#define SECT_ "{}::{}"\n'.format( "::".join(namespaces), base ) )
                    outf.write( '\n' )
                elif ( line.find( trace_fn ) != -1 ):
                    outf.write( '#define ' + base + 'TraceEvent(a) CPL_SYSTEM_TRACE_MSG( SECT_, ( "Old State=%s, Event=%s", getNameByState(getInnermostActiveState()), FsmTraceEvents[a] ));\n' )
                elif ( line.find( enum ) != -1 ):
                    pass
                elif ( line.find( comment ) != -1 ):
                    pass
                else:
                    outf.write( line )
                
    os.remove( old_trace_headerfile )
    os.rename( tmpfile, old_trace_headerfile )
     
     
     
#------------------------------------------------------------------------------
def getContextMethods( fname ):
    actions = []
    guards  = []
    with open(fname) as f:
        for line in f:
            g = re.search(r'[a-zA-Z0-9]+\(\)(?!\;)',line)
            a = re.search(r'[a-zA-Z0-9]+\(\)\;', line)
            if ( g != None ):
                guards.append( g.group(0) )
            if ( a != None ):
                actions.append( a.group(0).split(';')[0] )
    
    # Remove any duplicates from the grep'd methods
    return sorted(list(set(actions))), sorted(list(set(guards)))

def path_namespaces( namespaces ):
    flat = ''
    for n in namespaces:
        flat += n + "/"

    return flat

def flatten_namespaces( namespaces ):
    flat = ""
    for n in namespaces:
        flat += n + "_"

    return flat

def nested_namespaces( namespaces ):
    nest = ""
    for n in namespaces:
        nest += "namespace {} {} ".format(n,'{')

    return nest
    
def end_nested_namespaces( namespaces ):
    nest = ""
    for n in namespaces:
        nest += "};"
    nest += "  /// end namespace(s)"
    return nest

def cfg_namespaces( namespaces ):
    nest  = "*"
    for n in namespaces:
        if ( nest == "*" ):
            nest = n + " " 
        else:
            nest += "{} namespace {} ".format('{',n)

    return nest
    
def end_cfg_namespaces( namespaces ):
    nest  = ""
    count = len(namespaces)
    if ( count > 1 ):
        for n in range(1,count):
            nest += "};"
    
    return nest
    

def generatedContextClass( class_name, namespaces,  header, actions, guards ):
    fname = class_name + '.h'
    flat  = flatten_namespaces(namespaces)
    with open(fname,"w") as f:
        f.write( "#ifndef {}{}x_h_\n".format( flat, class_name ) )
        f.write( "#define {}{}x_h_\n".format( flat, class_name ) )
        f.write( header )
        f.write( "\n\n/* This file is auto-generated DO NOT MANUALLY EDIT this file! */\n\n" )
        f.write( "\n" )
        f.write( "/// Namespace(s)\n" );
        f.write( "{}\n".format( nested_namespaces(namespaces) ) )
        f.write( "\n\n" )
        f.write( "/// Context (aka actions/guards) for my Finite State Machine\n" )
        f.write( "class {}\n".format( class_name ) )
        f.write( "{\n" )
        f.write( "public:\n" )
        for a in actions:
            f.write( "    /// Action\n" )
            f.write( "    virtual void {} throw() = 0;\n".format( a ) )
            f.write( "\n" );
        f.write( "\n" );
        f.write( "public:\n" )
        for g in guards:
            f.write( "    /// Guard\n" )
            f.write( "    virtual bool {} throw() = 0;\n".format( g ) )
            f.write( "\n" );
        f.write( "\n" );
        f.write( "public:\n" )
        f.write( "    /// Virtual Destructor\n" )
        f.write( "    virtual ~{}(){}{}\n".format( class_name, "{","}" ) )
        f.write( "\n" );
        f.write( "};\n" )
        f.write( "\n" );
        f.write( "{}\n".format( end_nested_namespaces(namespaces) ) )
        f.write( "#endif /// end header latch\n" )
         
    


#------------------------------------------------------------------------------
def geneatedCodegenConfig( fname, base, names ):
    cfg = '''# Output configuration options for the given language. Pipe them into a file for further use!
#
#Allows to define naming conventions for events
PrefixEvents=
#
#Allows to define naming conventions for simple states
PrefixSimpleStates=
#
#Allows to define naming conventions for composite states
PrefixCompositeStates=
#
#Allows to define naming conventions for choice states
PrefixChoice=

#
#Path to 'dot.exe'.
#DotPath="C:\\Program Files\\Graphviz2.22\\bin\\dot.exe"
#DotPath=/usr/local/bin/dot
DotPath=
#
#Port the graphical statediagram.simulator listens for event strings. 
UdpPort=4445
#
#Options 'yes' and 'no' are possible. If set to 'yes' only hot transitions are shown
ShowOnlyHotTransitions=no
#
#It is possible to limit the length of the event text. This keeps the image compact.
NumberOfTransitionChars=32
#
#If set to 'yes' only correct models can be saved.
SaveCheckedOnly=yes
#
#If set to 'yes' action code is displayed in the state diagram of the integrated statediagram.editor.
DisplayEntryExitDoCode=yes
#
#Limit action code in the integrated statediagram.editor to the given number of chars.
NumberOfEntryExitDoCodeChars=32
#
#

#Defines the text each generated file starts with.
Copyright=$$HEADER$$
#
#Defines if real tabs or spaces are used for indentation.
Realtab=no
#
#If realtab is 'no' this key defines how many spaces to use per tab
Tabsize=4
#
#Some systems can use special compiler keywords to place the debug strings in program memory or a specifc segment
TypeOfDbgString=const char
#
#If set to 'no' the data and time info is supressed in each file header
IncludeDateFileHeaders=no

#
#Optional namespace used in the generated C#, Java and C++ file.
Namespace=$$NAMESPACE_START$$
NamespaceEnd=$$NAMESPACE_END$$
#
#Define a base classes for the generated machine class.
BaseClassMachine=$$BASE$$

#
#Define an optional base classes for the generated state classes.
BaseClassStates=
#
#If set to yes virtual create methods are gen- erated in the factory class.
CreateFactoryMethodsVirtual=No
#
#If set to yes all state classes are generated into a single cpp/h file.
CreateOneCppStateHeaderFileOnly=Yes
#
#If set to 'yes' a destructor for the state mchine class is generated. If set to 'virtual' a virtual destructor is generated. If set to 'no' no destructor is generated.
StateMachineClassHasDestructor=no
#
#If set to 'yes' separte state classes are used. Otherwise action code is completely inlined into the state machine code
SeparateStateClasses=no
#
'''
    # Replace tokens
    cfg = cfg.replace( "$$BASE$$", base )
    cfg = cfg.replace( "$$HEADER$$", getHeaderCfg() )
    cfg = cfg.replace( "$$NAMESPACE_START$$", cfg_namespaces(names) )
    cfg = cfg.replace( "$$NAMESPACE_END$$",   end_cfg_namespaces(names) )
    
    # create file
    with open(fname,"w") as f:
        f.write( cfg )

    

#------------------------------------------------------------------------------
def getHeader():
    return  '/*-----------------------------------------------------------------------------\n* This file is part of the Colony.Core Project.  The Colony.Core Project is an\n* open source project with a BSD type of licensing agreement.  See the license\n* agreement (license.txt) in the top/ directory or on the Internet at\n* http://integerfox.com/colony.core/license.txt\n*\n* Copyright (c) 2014, 2015  John T. Taylor\n*\n* Redistributions of the source code must retain the above copyright notice.\n*----------------------------------------------------------------------------*/\n/** @file */\n\n'

def getHeaderCfg():
    return r'/*-----------------------------------------------------------------------------\n* This file is part of the Colony.Core Project.  The Colony.Core Project is an\n* open source project with a BSD type of licensing agreement.  See the license\n* agreement (license.txt) in the top/ directory or on the Internet at\n* http://integerfox.com/colony.core/license.txt\n*\n* Copyright (c) 2014, 2015  John T. Taylor\n*\n* Redistributions of the source code must retain the above copyright notice.\n*----------------------------------------------------------------------------*/\n/** @file */\n\n'

