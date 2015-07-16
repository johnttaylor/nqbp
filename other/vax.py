#!/usr/bin/python
"""Invokes NQBP's vax_base.py script.  Place 'vax.py' in your current directory or in your command path

import os
import sys

# Make sure the environment is properly set
NQBP_BIN = os.environ.get('NQBP_BIN')
if ( NQBP_BIN == None ):
    sys.exit( "ERROR: The environment variable NQBP_BIN is not set!" )
sys.path.append( NQBP_BIN )

# Find the Package & Workspace root
from other import vax_base
vax_base.run( sys.argv )

