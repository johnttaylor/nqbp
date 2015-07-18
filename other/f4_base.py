#!/usr/bin/env python
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
f4 - Forms For files.  Generates a text file from template file(s) and dynamic 
     user input.
===============================================================================
Usage: f4 [options] <tname> [-o OUTFILE] -f MAPFILE
       f4 [options] <tname> [-o OUTFILE] map <entries>...
       f4 --guide


Arguments:

  <tname>          Name of the template file to expand.
  -o OUTFILE       Name of the output file that contains the result of the
                   expansion.  If no output is specified, then the output
                   is STDOUT.
  map              Keyword that marks the start of Substituion map entries.
  <entries>        The values for the Substitution Map.  Each entry is 
                   seperated by white space.  Quotes can be used to define
                   entries that contain whitespace.
  -f MAPFILE       Name of the file that contains the entries for the 
                   Substitution Map.  The format of the file is that each
                   line is entry in the Map.  No comments or blank lines
                   are allowed in the file.                  
Options:

  -d DELIMITER     Sets the delimiter for seperating multi-value map entry.  
                   [Default: ,]  
  -r ROOTPATH      Sets the 'root path' for the _RELPATH token. The default
                   is no root path, i.e. root path = current working directory.
  --local PATH     Sets the local search path when trying to open/find the  
                   specified template file and/or subscript template files.
  --global PATH    Sets the global search path when trying to open/find the
                   specified template file and/or subscript template files.
  --outcast-pkg    Sets the 'root path' for the _RELPATH token to the current
                   Package as defined by the Outcast command: 'orc --qry-pkg'
  -?, --guide      Display user guide.
  -h, --help       Display command help.
        
   
NOTES:
    o The search order for template files is as follows:
        1) The current working directory is searched first
        2) Then the --local PATH (if there is one)
        3) Finally the --global PATH (if there is on)

              
"""

#
import subprocess
import re
import sys

#------------------------------------------------------------------------------
# Parse command line
def run( argv ):

    # Process command line args...
    args = docopt(usage, version="0.0.1" )
    print args

    # Print guide
    if ( args['--guide'] ):
        print guide
        sys.exit()
        
    # Build the Header (i.e. parse the list of token IDs for the template)
    header, infd = build_header_from_file( args )
    print header

    # Build the Substitution Map
    smap = build_map( args )
    print smap
   
    # Expand the template file
    outfd = Stdout( args['-o'] )
    expand_template( infd, header, smap, outfd, args )

    # housekeeping
    infd.close()
    outfd.close()

#------------------------------------------------------------------------------
def expand_template( infd, header, smap, outfd, args ):
    lnum = 0
    for l in infd:
        eline = expand_line( l, header, smap, outfd, lnum, args )
        if ( eline != None ):
            outfd.write( eline )
        lnum += 1


def expand_line( line, header, smap, outfd, lnum, args ):
    outline = ""
    escaped = False

    # Loop though all characters in the line
    idx   = 0
    count = len(line)
    while( idx < count ):

        # Handle esacping the mark & escape characters
        if ( escaped ):
            outline += line[idx]
            idx     += 1
            esacped  = False

        elif ( line[idx] == header.get_esc() ):
            escaped  = True
            idx     += 1
            
        # Check for Subscripting
        result = subscripting( line, idx, header, smap, outfd, lnum, args )
        if ( result == None ):
            return None

            
        # Found the mark character
        elif ( line[idx] == header.get_mark() ):
            text, consumed_count = substitute_token( line[idx+1:], header, smap, idx, lnum, args )
            outline += text
            idx     += consumed_count + 1
            
        # literal text
        else:
            outline += line[idx]   
            idx     += 1
            
    return outline
    
        
def substitute_token( line, header, smap, col, lnum, args ):
    # extract the token
    end = line.find( header.get_mark() )
    if ( end == -1 ):
        sys.exit( "ERROR: Bad token specified at #CONTENT line offset# {}, col# {}".format( lnum, col+1 ) ) 
    token     = line[:end]
    end_idx   = end
    consumed  = len(token) + 1
    start_idx = 0

    # Housekeeping
    lcmd      = None
    loper     = None
    rcmd      = None
    roper     = None

    # extract the L-Command (if there is one)
    lmark = line.find( '<' )
    if ( lmark != -1 ):
        lcmd     = line[0:1]
        loper    = line[1:lmark]
        start_idx = lmark+1

    # extract the R-Command (if there is one)
    rmark = line.find( '>' )
    if ( rmark != -1 ):
        end_idx = rmark
        rcmd   = line[rmark+1:rmark+2]
        roper  = line[rmark+2:-2]
 
    # extract the token_id
    token_id = line[start_idx:end_idx]
                 
    # Check for special tokens
    if ( token_id.startswith( '_' ) ):
        entry = process_special_token( token_id, args )
       
    # Look-up token id
    else:
        tidx = header.find_token( token_id )
        if ( tidx == -1 ):
            sys.exit( "ERROR: Token - {} - not defined in the template header (line offset={}, col={}).".format( token_id, lnum, col+1 ) )
        entry = smap.get_entry( tidx )

    # Expand value
    new_value = entry.get_value()
    # apply L-command
    # apply R-Command


    # Return final value
    return new_value, consumed


def process_special_token( token_id, args ):
    return None

def subscripting( line, idx, header, smap, outfd, lnum, args ):
    return False

#------------------------------------------------------------------------------
def build_map( args ):
    # Select source of the map
    if ( args['-f'] ):
        input = open_map_file( args['-f'] )
    elif( args['<entries>'] ):
        input = args['<entries>'] 
    else:
        sys.exit( "ERROR: No substitution map entries provided. Use 'f4 -h' for help" )

    # build the map
    smap = SMap( args['-r'], args['-d'] )
    for entry in input:
        e = SMapEntry( normalize_entry( entry ), args['-d'] )
        smap.add_entry( e )

    return smap


def normalize_entry( raw_entry ):
    e = raw_entry.strip();
    if ( e.startswith('"') and e.endswith('"') ):
        e = e[1:-1]
    elif ( e.startswith("'") and e.endswith("'") ):
        e = e[1:-1]
    
    return e
                        
def open_map_file( fname ):
    try:
        inf = open( fname )
        return inf;
    except EnvironmentError:
        sys.exit( "ERROR: Cannot open substitution map input file: {}".format( fname ) )


#------------------------------------------------------------------------------
def build_header_from_file( args ):
    template     = args['<tname>']
    header       = None
    header_found = False
    try:
        infile = open_template_file( template, args )
        for line in infile:
            if ( line.startswith(';') ):
                pass
            elif ( not line.strip() ):
                pass
            elif ( line.startswith( '#HEADER' ) ):
                header       = process_header( line, args )
                header_found = True
            elif ( header_found and line.startswith( '#CONTENT') ):
                return header, infile
            elif ( header_found ):
                header.add_token( line.strip().split(',')[0] )

            
    except EnvironmentError:
        infile.close()
        sys.exit( "ERROR: Cannot read from template file: {}".format( template ) )

    # If I get here than the template file is malformed.
    infile.close()
    sys.exit( "ERROR: Invalid Template file ({}).  Missing #HEADER and/or #CONTENT markers.".format( template ) )
    

def process_header( line, args ):
    options = line.split(',')
    count   = len(options)
    mark    = '$'
    esc     = '`'

    # Override default options
    if ( count > 1 ):
        mark = options[1].strip()
        if ( count > 2 ):
            esc = options[2].strip()

    return Header( mark, esc )
        

def open_template_file( fname, args ):
    # Search CWD
    try:
        inf = open( fname )
        return inf;
    except EnvironmentError:
        pass
            
    # Search local path
    if ( args['--local'] ):
        try:
            f = os.path.join( args['--local'], fname )
            inf = open( f )
            return inf
        except EnvironmentError:
            pass

    # Search global path
    if ( args['--global'] ):
        try:
            f = os.path.join( args['--global'], fname )
            inf = open( f )
            return inf
        except EnvironmentError:
            pass

    # If I get here -->could not find the requested template file
    sys.exit( "ERROR: Cannot open/find template file: {}".format( fname ) )
    
          
class Header(object):
    def __init__( self, mark, esc ):
        self.num_tokens = 0
        self.mark       = mark
        self.esc        = esc
        self.tokens     = []

    def get_mark( self ):
        return self.mark

    def get_esc( self ):
        return self.esc

    def add_token( self, token_name ):
        self.tokens.append( token_name )
        self.num_tokens += 1

    def find_token( self, name ):
        idx = 0
        for n in self.tokens:
            if ( n == name ):
                return idx
            idx +=1

        # If I get here -->no matching token
        return -1

    def __repr__(self):
        ret = "HEADER: count={}, mark={}, esc={}, Tokens={}".format( self.num_tokens, self.mark, self.esc, self.tokens )
        return ret


#------------------------------------------------------------------------------
class SMapEntry(object):
    def __init__( self, value, delimiter, force_no_iter_count=False ):
        self.org       = value
        self.values    = value.split(delimiter)
        self.count     = len(self.values)
        self.itercount = self.count
        if ( force_no_iter_count ):
            self.itercount = 1
    
    def get_value(self, index = 0 ):
        if ( index >= self.count ):
            index = self.count - 1
        return self.values[index]

    def get_raw_value( self ):
        return self.org
             
    def get_count(self):
        return self.count

    def get_iter_count(self):
        return self.itercount

    def __repr__(self):
        ret = "ENTRY: count={}, icount={}, values={}".format( self.count, self.itercount, self.values )
        return ret


class SMap(object):
    def __init__( self, rootpath, delimiter=',' ):
        self.num_entries = 0
        self.root_path   = rootpath
        self.delimiter   = delimiter
        self.entries     = []
        
    def add_entry( self,  entry_object ):
        self.entries.append( entry_object )
        self.num_entries += 1
        
    def get_num_entries( self ):
        return self.num_entries

    def get_entries( self ):
        return self.entries

    def get_entry( self, index ):
        if ( index >= self.num_entries ):
            return None
        else:
            return self.entries[index]

    def get_root_path( self ):
        return self.root_path
                
        
    def __repr__(self):
        ret = "SMAP: count={}, del={}. Entries={}".format( self.num_entries, self.delimiter, self.entries )
        return ret


#------------------------------------------------------------------------------
class Stdout(object):
    def __init__( self, outname=None ):
        if ( outname != None ):
            try:
                self.handle = open( outname, 'w' )
            except EnvironmentError:
                self.handle = None
                sys.exit( "ERROR: Cannot open output file: {}".format( outname ) )
        else:
            self.handle = sys.stdout

    def write( self, data ):
        if ( self.handle != None ):
            self.handle.write( data )
        else:
            sys.exit( "ERROR: Invalid output handle" )
         
    def close( self ):
        if ( self.handle is not sys.stdout ):
            self.handle.close()     
            
                
#------------------------------------------------------------------------------
guide = r"""
F4 USER GUIDE
===============================================================================
F4 takes an input template and a user supplied Substitution Map and generates
an output file by replacing token identifiers within the template file with
values from the Substitution Map.

F4 is an updated, python version of the Jcl ASX command line applet. ASX in 
turn was inspired from the VAX FMS (Forms Management System).  So yes, you can 
teach an old programmer new tricks as long as it is an old trick.



TEMPLATE FILE FORMAT:
-----------------------------------
#HEADER [,<mark_char>][,<esc_char>]
tokenid_0 [,description comment]
tokenid_1 [,description comment]
...
tokenid_n [,description comment]
#CONTENT
<all lines after the #CONTENT marker are expanded literally to the output
 file.  When one of the above tokenid is encountered, the token is
 replace with its corresponding text from the Substitution Map. >

---------------------------------------


mark_char:=         A one character symbol used to indicate the start of a 
                    token. The default mark character is '$'.

esc_char:=          Escape character used to embedded a literal mark and/or 
                    escape characters.  The default escape character is '`'

tokenid_n:=         Identifier for a token. Tokens are match up with the 
                    Substitution Map by their order listed.  That is the first 
                    token listed maps to index 0 in the Subsitution map, second
                    token maps to index 1, etc. Token identifier can be 
                    any alpha-numeric string that does NOT start with a '_' or 
                    contain spaces. There is are reserved token identfiers.  
                    All reserverd token identifiers start with a leading '_'.

NOTE: Comment lines and Blank lines are ignored from the top of the file
      until the #CONTENT marker is encounters.  Comment lines start with
      a ';'.



REPLACEMENT TOKEN SYNTAX:
-------------------------
The following syntax is used within the #CONTENT section of the template to
embedded token identifiers.

<mark>[<lcmd>[<operand>]<]<tokenid>[><rcmd>[operand]<mark>
<esc><mark>
<esc><esc>

Where:
    <mark>      Is the mark character defined by the #HEADER statement.  All
                embedded token IDs start with a mark character.  
            

    <esc>       Is the escape character defined by the #HEADER statement. The
                escape character is used to embedded a literal mark and/or
                escape characters in the #CONTENT section.

    <lcmd>      Single character that selects an optional L-Command.  See 
                below for a list of L-Commands.

    <operand>   Optional string input for L/R-Commands.
                
    <tokenid>   One of the token identifiers defined in the #HEADER section.
                Also a string literal (encapsulated in single or double quotes)
                can be used in lieu of a token identify.  When this is done the
                string literal is the substitution value.  Typically this is
                done when it is desirable to apply an L or R command to fixed
                string.
               
    <rcmd>      Single character that selects an optional R-Command.  See 
                below for a list of R-Commands.

    Examples:
        Given: className="bob", namspeaces="Rte,Db,Set"

            $className$        expands to: "bob"
            $u<className>$     expands to: "Bob"
            $namespaces>+::$   expands to: "Rte::Db::Set" 



ITERATION:
----------
Iteration of the #CONTENT section is done by specifying two or more values for
at least one of the entries in the Substitution Map.  The Substitution Map 
defines a single character that is used to delineate multi-vaules in a single
entry.  The default delimiter character is ','.   The  number of iterations
that occur is the number of delimiter characters contained  in the substitution
text + 1.  When more than one Substitution map entry contains multiple values,
then the number of iteration is the maximum of the combined iterators.  If an
multi-valued entry exhausted its lists before the overall iteration process is
finished, its  last value is used for the remaining iterations.

Iteration can also be 'forced' by using the S-Command "iter" when invoking a
subscript (see below for details about S-Commands).  The number of iterations
performs is the maximum iteracount derived from the Substitution Map and the
'iter' S-Command. 

NOTE: Iteration ONLY APPLIES to subscripts.  The iteration rules are not 
      applied when processing the top level template.




SPECIAL TOKENS:
---------------
The following are special predefined tokens that can be used in the '#CONTENT'
section.  
_YYYY       - Embeds the current year in with the following format: '%04d'
_MM         - Embeds the current month in with the following format: '%02d'
_DD         - Embeds the current day in with the following format: '%02d'
_ITERNUM    - Embeds the iteration number with the following format: '%d'. The
              vaule of the iteration number always starts at zero.
_ITERVAL    - Embeds the iteration counter value with the following format: '%d'
_ABSPATH    - Embeds the absolute path of the current working directory.  The
              directory seperator will always be "/"
_ABSPATH_N  - Same as _ABSPATH, except the native directory seperator is used.
_RELPATH    - A multi-value token that contains a directory path - where each
              directory in the path is a value - of current working directory
              relative to a 'root directory' that is specified when the
              Substitution Map is created. For example:
                Given: 
                    1) The CWD is: c:\_workspaces\zoe\src\Cpl\Bob
                    2) The 'root directory' is: c:\_workspaces\zoe\src
                
                    Then: _RELPATH = "Cpl,Bob"
            



L-COMMANDS:
----------------
L-Commands allow an operation to be performed on the value being subsituted.
For example, the token operator 'U', will convert the value to all uppercase
letters before being substituted into the output file.  A token operator is
specified by a character pair of the token seperator and operator character
immediately following  the initial token seperator.  For example: To apply the
uppercase operator to the token - 'name' - use: $U.name.  The following is a
list of currently supported L-Commands:

    U   - upper case token value
    L   - lower case token value
    u   - Force the FIRST character in the token value to upper case
    l   - Force the FIRST character in the token value to lower case
    +   - Adds the value the L-cmd operand parameter to the substitution value.
          If the substitution value is not a numeric value, nothing is done.
    -   - Subtracts the value the L-cmd operand parameter to the substitution 
          value. If the substitution value is not a numeric value, nothing is 
          done.



R-COMMANDS:
--------------
R-Commands perform posfix operations on the replacement being done.  The
following is list of currently supported R-Commands.  A single substitution can
include both L and R commands with the L command being performed (on all
values) before the R command is performed.

    f   - First Only.  This command substitues the token identifier's value 
          ONLY on the first iteration.  All other iterations, an empty string 
          is substituted.
          
    F   - Not First.  This command substitues the token identifier's value 
          on all iterations EXCEPT the first iteration. On the first iteration
          an empty string is substituted.

    l   - Last Only.  This command substitues the token identifier's value 
          ONLY on the last iteration.  All other iterations, an empty string 
          is substituted.
          
    L   - Not Last.  This command substitues the token identifier's value 
          on all iterations EXCEPT the last iteration. On the last iteration
          an empty string is substituted.

    :   - Indexing. This command will select the Nth value from a multi-valued
          token.  This command takes a 'index' operand that is zero based 
          index.  If the token identifier is not a multi-valued entry or the 
          'index' value exceeds the entrys range - then last (only) value is
          used for the substitution.

            Given token: names="bob,henry,fred"
            
                $names>:0$    results in: "bob"
                $names>:32$   results in: "fred"
                $u<names>:1$  results in: "Henry"
       
       
    +   - Concatention. This command will expand a multi-value into a single 
          value when the token is replaced.  The command takes an optional
          'string' operand that will be inserted between the individual 
          expanded values.  There is no trailing 'string' when used. Examples:
            
            Given token: names="bob,henry,fred"
            
                $names>+$     results in: "bobhenryfred"
                $names>+, $   results in: "bob, henry, fred"
                $U<names>+_$  results in: "BOB_HENRY_FRED"



SUBSCRIPTS:
----------
The expander supports nesting templates within templates. Special/reserved 
token identifiers are used to invoke the nesting process.  The "subscripting"
process also support iteration when expanding the subscript.  The following
are the different forms that can be used to 'invoke' a subscript.

NOTE: When the subscripting occurs, the entire contents of the subscript is
      "embedded" into its parent script with the same indentation level as
      the "$_SUBSCRIPT" token.


FORMAT #1 - Reference an external template file

    <mark>_SUBSCRIPT,<fname> [,[*]<tokenA>[,[*]<tokenB>]....[,[*]<tokenN>]:[<scmd> [<args>...]]*
    
    Where:
        fname:=   File name of the template to include.  The template file is
                  assumed to be the cwd (current-working-directory) or 'fname'
                  is an absolute path.
                  
        tokenA:=  The current iteration substitution value of "tokenA" is used 
                  as the  first entry in the  substitution map of for the
                  sub-script that will be  expanded.  The current substitution
                  value of "tokenB" is used as the second  entry in the
                  substitution map, etc.  ITERATION NOTE: If a leading '*'
                  characacter is used when specifying the token name, then ALL 
                  values of the token are used to create the entry in the 
                  substituion map AND the entry will NOT trigger the iteration
                  mechnaism for the subscript.  If the iteration mechanism is
                  trigger via a different multi-valued (non leading '*') token,
                  the multi-valued tokens that start with a '*' will be treated
                  as single valued token with respect to iteration within the
                  subscript.
                   
        scmd      A S-Command string identifier followed by zero or more
                  command arguments.  Multiple S-Commands can be specified using
                  a comma to seperate the commands.  When multiple commands are
                  specified, there are executed if left to right order
                  
        args      Optional arguments to a S-Command.  Individual arguments are
                  seperated by spaces.
                  
                  

FORMAT #2 - Inlined Subscript

    <mark>_INLINE [,[*]<tokenA>[,[*]<tokenB>]....[,[*]<tokenN>]:[<scmd> [<args>...]]*
    .....
    <mark>_END_INLINE
     
    
    Subscripts can be inlined.  This is done by place the content of the
    'subscript file' between the start-of-subscript-line marker and the
    end-of-subscript-line marker.  The start-of-subscript-line marker is:
    "$_INLINE,...".  The end-of-subscript-line marker is "$_END_INLINE". 
    
    The #HEADER section of inlined subscripts are implied using the following
    rules:
        1) num_tokens is determined by the number of tokens supplied with
           '$_INLINE' statement.
        2) The mark_char, esc_char, and iteration_char values are inherited
           from the parent template's #HEADER section
        3) The token identifier names are set/assumed to match the names of 
           the tokens supplied on the '$_INLINE' statement.
              
    NOTE: For the indentation to work properply TABS can not be used as leading 
          characters in the contents of the inlined subscript! 


S-COMMANDS:
--------------
S-Commands modify/aguments the behavior when invoking subscripting. The 
following is a list of currently supported S-Commands:

    Explicit Iteration:
    
        iter [<start> [<step> [<min_iters>]]] 
    
        This command forces iteration on subscript.  The <start> value is
        a numeric value for the initial value of the _ITERVAL token.  The
        default for <start> is 0.  The <step> value is the step that _ITERVAL
        is increment on subsequent iterations.  The default for <step> is 1.
        The <min_iters> value forces at least that many iterations.  The 
        default value for <min_iters> is 0. The actual number of iteration is 
        the maximum of <min_iters> value and the iteration count derived from 
        the Substitution Map. 
        
        
        

EXAMPLES
===============================================================================

**** EXAMPLE#1 ****

Simple Template with token operator
-------------------------------------------
; Simple Script
#HEADER

className
flagName,  Name of the flag variable 

; Begin Expansion Text
#CONTENT
class $u<className$
{
public:
    bool $l<flagName$;
};
-------------------------------------------

GIVEN: 
    className:= 'bob'
    flagName:=  'Foobar'
    
RESULT:
-------------------------------------------
class Bob
{
public:
    bool foobar;
};
-------------------------------------------



**** EXAMPLE#2 ****

Template With External Subscripting
-------------------------------------------
; Nested Script
#HEADER,%,~

embeddedClassName, Name of the embedded class
flagName,          Name of the flag variable for the above class
myClass            Name of My class that will contain the embedded class

; Begin Expansion Text
#CONTEXT
class %myClass%
{
    %_SUBSCRIPT, simpleScript, embeddedClassName, flagName
};
-------------------------------------------

GIVEN: 
    embeddedClassName:= 'oak'
    flagName:=          'Foobar'
    myClass:=           'bob'
    
RESULT:
-------------------------------------------
class bob
{
    class Oak
    {
    public:
        bool foobar;
    };
};
-------------------------------------------



**** EXAMPLE#3 ****

Template With Subscripting Iteration (the subscript is repeated N time, 
once for each name in 'embeddedNames')
-------------------------------------------
; Nested Script with iteration
#HEADER

embeddedNames,     Names of the N class to embedded. Each name is seperated 
;                  with ',' (Foo,Foo2,...)
flagName,          Name of the flag variable for the above class
myClass            Name of My class that will contain the embedded class

; Begin Expansion Text
#CONTENT
class $myClass$
{
    $_SUBSCRIPT, simpleScript, embeddedNames, flagName
};
-------------------------------------------

GIVEN: 
    embeddedNames:= 'oak,pine,willow'
    flagName:=      'foobar'
    myClass:=       'bob'
    
RESULT:
-------------------------------------------
class bob
{
    class Oak
    {
    public:
        bool foobar;
    };
    class Pine
    {
    public:
        bool foobar;
    };
    class Willow
    {
    public:
        bool foobar;
    };
};
-------------------------------------------


**** EXAMPLE#4 ****

Script With Inlined Subscripting
-------------------------------------------
; Simple Script
#HEADER
className
flagName,  Name of the flag variable 

; Begin Expansion Text
#SCRIPT
class $u.className
{
public:
    bool m_$l<flagName$;

    $_INLINE, className, flagName
    void $u<className$::set$u<flagName$( bool newvalue  );
    $_END_INLINE
    
public: // MORE stuff here
};
-------------------------------------------

GIVEN: 
    className:=     'bob'
    flagName:=      'foobar'
    
RESULT:
-------------------------------------------
class Bob
{
public:
    bool m_foobar;
    
    void Bob::setFoobar( bool newvalue );
    
public: // MORE stuff here
};
-------------------------------------------

"""

    