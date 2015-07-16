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
vax - Generates a text file from template file(s) and dynamic user input
===============================================================================
Usage: vax [options] ...

Arguments:
                   
Options:
  -?, --guide      Display user guide.
  -h, --help       Display command help.
        
         
NOTES:
      
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
    
    if ( args['--guide'] ):
        print guide
        sys.exit()
        
    print "I don't do anything right now!"


#------------------------------------------------------------------------------
guide = r"""
VAX USER GUIDE
===============================================================================
Vax takes an input template and a user supplied Substitution Map and generates
an output file by replacing token identifiers within the template file with
values from the Substitution Map.


TEMPLATE FILE FORMAT:
-----------------------------------
#HEADER, <num_tokens> [,<mark_char>,<esc_char>][,<iteration_char>]
tokenid_0 [,description comment]
tokenid_1 [,description comment]
...
tokenid_n [,description comment]
#CONTENT
<all lines after the #CONTENT marker are expanded literally to the output
 file.  When one of the above tokenid is encountered, the token is
 replace with its corresponding text from the Substitution Map. >

---------------------------------------


num_tokens:=        Number of Tokens in the file.

mark_char:=         A one character symbol used to indicate the start of a 
                    token. The default mark character is '$'.

esc_char:=          Escape character used to embedded a literal mark and/or 
                    escape characters.  The default escape character is '`'

iteration_char:=    A one character symbol used to delineate multiple values 
                    within a single entry in the Substitution Map.  By using
                    the iteration character the user creates a multi-valued
                    Substitution Map entry.  Multi-valued entries can invoke
                    iteration with expanding a token/sub-script entry.  The
                    default iteration character is ','.

tokenid_n:=         Identifier for a token. Tokens are match up with the 
                    Substitution Map by their order listed.  That is the first 
                    token listed maps to index 0 in the Subsitution map, second
                    token maps to index 1, etc.  Token identifier can be 
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

<mark>[<lcmd>[<operand>].]<tokenid>[.<rcmd>[operand]<mark>]
<esc><mark>
<esc><esc>

Where:
    <mark>      Is the mark character defined by the #HEADER statement.  All
                embedded token IDs start with a mark character.  A Trailing
                mark character is only needed when using an R-Command.

    <esc>       Is the escape character defined by the #HEADER statement. The
                escape character is used to embedded a literal mark and/or
                escape characters in the #CONTENT section.

    <lcmd>      Single character that selects an optional L-Command.  See 
                below for a list of L-Commands.

    <operand>   Optional string input to Commands.
                

    

ITERATION:
----------
Iteration of the #CONTENT section is done by specifying two or more values for
the  substitution text of one or more tokens.  Each substitution value is
separated by the iteration character that is specified in the #HEADER
statement. The  number of iterations that occur is the number of iteration
characters contained  in the substitution text + 1.  When more than one
subsitution value contains multiple values, then the number of iteration is the
maximum of the combined iterators.  If an multi-valued entry exhausted its
lists before the overall iteration process is finished, its  last value is used
for the remaining iterations.




SPECIAL TOKENS:
---------------
The following are special predefined tokens that can be used in the '#CONTENT'
section.  
_YYYY    - Embeds the current year in with the following format: '%04d'
_MM      - Embeds the current month in with the following format: '%02d'
_DD      - Embeds the current day in with the following format: '%02d'
_COMMA   - Embeds a comma (",") except when the current iteration is the
           LAST iteration, then it returns an empty string.



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



R-COMMANDS:
--------------
R-Command perform posfix operations on the replacement being done.  The
following is list of currently supported R-Commands.  A single substitution can
include both L and R commands with the L command being performed (on all
values) before the R command is performed.

    >   - Concatention. This command will expand a multi-value into a single 
          value when the token is replaced.  The command takes an optional
          'string' operand that will be inserted between the individual 
          expanded values.  There is no trailing 'string' when used. Examples:
            
            Given token: names="bob,henry,fred"
            
                $names.>$     results in: "bobhenryfred"
                $names.>, $   results in: "bob, henry, fred"
                $U.names.>_$  results in: "BOB_HENRY_FRED"



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

    <mark>SUBSCRIPT,<fname> [,[*]<tokenA>[,[*]<tokenB>]....[,[*]<tokenN>]
    
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
                  substituion map.  
                  
                  

FORMAT #2 - Inlined Subscript

    <mark>INLINE [,[*]<tokenA>[,[*]<tokenB>]....[,[*]<tokenN>]
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




EXAMPLES
===============================================================================

**** EXAMPLE#1 ****

Simple Template with token operator
-------------------------------------------
; Simple Script
#HEADER,2

className
flagName,  Name of the flag variable 

; Begin Expansion Text
#CONTENT
class $u.className
{
public:
    bool $l.flagName;
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
#HEADER,3,%,~

embeddedClassName, Name of the embedded class
flagName,          Name of the flag variable for the above class
myClass            Name of My class that will contain the embedded class

; Begin Expansion Text
#CONTEXT
class %myClass
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
#HEADER,3

embeddedNames,     Names of the N class to embedded. Each name is seperated 
;                  with ',' (Foo,Foo2,...)
flagName,          Name of the flag variable for the above class
myClass            Name of My class that will contain the embedded class

; Begin Expansion Text
#CONTENT
class $myClass
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


Script With Inlined Subscripting
-------------------------------------------
; Simple Script
#HEADER,2
className
flagName,  Name of the flag variable 

; Begin Expansion Text
#SCRIPT
class $u.className
{
public:
    bool m_$l.flagName;

    $_INLINE, className, flagName
    void $u.className::set$u.flagName( bool newvalue  );
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

    