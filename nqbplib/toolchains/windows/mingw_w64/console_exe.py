#------------------------------------------------------------------------------
# TOOLCHAIN
#
#   Host:       Windows
#   Compiler:   Mingw_w64
#   Target:     Windows
#   Output:     64 bit Console application
#------------------------------------------------------------------------------

import sys
from nqbplib import base
from nqbplib import utils


class ToolChain( base.ToolChain ):
    def __init__( self, exename, prjdir, build_variants, default_variant='release' ):
        base.ToolChain.__init__( self, exename, prjdir, build_variants, default_variant )
        self._ccname = 'Mingw_W64'
        
        # statically link my C/C++ libraries
        self._base_release.cflags  = self._base_release.cflags + ' -Wl,-static-libgcc -Wl,-static-libstdc++ '
        
        #
        # Build Config/Variant: "xyz"
        #
       
        # Common/base options, flags, etc.
        
        #self._base_xyz = self._base_release.copy()
        #self._base_xyz.cflags  = '-c -DBUILD_TIME_UTC={:d}'.format(self._build_time_utc)
        
        # Optimized options, flags, etc.
        #self._optimized_xyz = self._optimized_release.copy()
        
        # Debug options, flags, etc.
        #self._debug_xyz = self._debug_release.copy()
        
        # Create new build variant - but ONLY if it DOES NOT already exist
        #if ( not self._bld_variants.has_key('xyz') ):
        #    self._bld_variants['xyz'] = { 'nop':'none' }
            
        # Add to dictionary of options for the 'xyz' build variant
        #self._bld_variants['xyz']['base']      = self._base_xyz
        #self._bld_variants['xyz']['optimized'] = self._optimized_xyz
        #self._bld_variants['xyz']['debug']     = self._debug_xyz

    #--------------------------------------------------------------------------
    def validate_cc( self ):
       t = base.ToolChain.validate_cc(self)
       if ( not 'x86_64-w64-mingw32' in t[1] ):
           utils.output( "ERROR: Incorrect build of GCC (target does NOT equal 'x86_64-w64-mingw32')" )
           sys.exit(1)

       return t