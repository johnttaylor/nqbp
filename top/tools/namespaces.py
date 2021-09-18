#!/usr/bin/python3
"""
Package specific script that updates the 'pkg.namespaces' file with all of the
namespaces 'owned' by the package.  This script is called as part of the
publish package process.

Note: Package owner can opt for updating the 'pkg.namespaces' file as a
      manual process by having this script do nothing and simply 
      return '0'

Usage: namespaces <pkgroot>

Returns: If the update was successful then the script returns '0'; else
         a non-zero value is returned.
"""


#------------------------------------------------------------------------------
# 

# MAIN
if __name__ == '__main__':
    # No auto update of namespaces
    print( "No automatic update of namespaces." )


