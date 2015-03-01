#------------------------------------------------------------------------------
# TOOLCHAIN
#
#   Host:       Windows
#   Compiler:   KPit Cummins - GNU RX-ELF (default is to use newlib)
#   Target:     Renesas RX
#   Output:     .MOT file
#------------------------------------------------------------------------------

import sys
import os
from nqbplib import base
from nqbplib import utils

class ToolChain( base.ToolChain ):

    #--------------------------------------------------------------------------
    def __init__( self, exename, prjdir, build_variants, default_variant='release' ):
        base.ToolChain.__init__( self, exename, prjdir, build_variants, default_variant )
        self._ccname = 'KPit Cummins - GNU RX-ELF'
        self._cc       = 'rx-elf-gcc-wrapper'  
        self._ld       = 'rx-elf-gcc-wrapper'  
        self._asm      = 'rx-elf-gcc-wrapper'   
        self._ar       = 'rx-elf-ar'   
        self._objcpy   = 'rx-elf-objcpy'

        self._asm_ext  = 'asm'    
        
        self._clean_list.extend( ('x', 'mot') )
        
        # Get root of the final output name
        exename_base = os.path.splitext(exename)[0] 

        # Note: defaults to using 'newlib'
        self._base_release.cflags   = self._base_release.cflags + '-mcpu=rx600 -Wa,-alhs=ME_CC_BASE_FILENAME.lst'
        self._base_release.asmflags = self._base_release.cflags

        self._base_release.linklibs  = ' -Wl,--start-group -lnosys -lstdc++ -lgcc -lc -lm -Wl,--end-group '
        self._base_release.linkflags = '-nostartfiles -Wl,-Map=' + exename_base + '.map'

        self._debug_release.cflags   = self._debug_release.cflags + ' -D DEBUG'
        self._debug_release.asmflags = self._debug_release.cflags

        self._optimized_release.cflags = self._optimized_release.cflags + ' -fno-function-cse -funit-at-a-time -falign-jumps -fdata-sections -ffunction-sections -D RELEASE'
        self._optimized_release.asmflags = self._optimized_release.cflags
        self._optimized_release.linkflags = '--no-keep-memory --strip-debug'

        
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
    #def validate_cc( self ):
    #   t = base.ToolChain.validate_cc(self)
    #   if ( not 'i686-w64-mingw32' in t[1] ):
    #       utils.output( "ERROR: Incorrect build of GCC (Target does NOT equal 'mingw32')" )
    #       sys.exit(1)
    #
    #    return t
