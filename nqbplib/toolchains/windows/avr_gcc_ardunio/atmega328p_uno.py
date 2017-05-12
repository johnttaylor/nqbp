#------------------------------------------------------------------------------
# TOOLCHAIN
#
#   Host:       Windows
#   Compiler:   avr-gcc 
#   Target:     atmega-xxx / Ardunio
#   Output:     .HEX file
#------------------------------------------------------------------------------

import sys, os
from nqbplib import base
from nqbplib import utils

class ToolChain( base.ToolChain ):

    #--------------------------------------------------------------------------
    def __init__( self, exename, prjdir, build_variants, env_tools, default_variant='release', env_error=None ):
        base.ToolChain.__init__( self, exename, prjdir, build_variants, default_variant )
        self._ccname   = 'AVR-GCC-ATMega328p Ardunio'
        self._cc       = os.path.join( env_tools, 'hardware', 'tools', 'avr', 'bin', 'avr-gcc' )
        self._ld       = os.path.join( env_tools, 'hardware', 'tools', 'avr', 'bin', 'avr-gcc' )
        self._ar       = os.path.join( env_tools, 'hardware', 'tools', 'avr', 'bin', 'avr-ar' )
        self._objcpy   = os.path.join( env_tools, 'hardware', 'tools', 'avr', 'bin', 'avr-objcopy' )

        # Cache potential error for environment variables not set
        self._env_error = env_error;

        # set the name of the linker output (not the final output)
        self._link_output = '-o ' + exename.replace(".hex",".elf")

        # Define paths
        core_path = os.path.join(env_tools,'hardware', 'arduino', 'avr', 'cores', 'arduino' )
        hardware_path = os.path.join(env_tools, 'hardware', 'arduino', 'avr', 'variants', 'standard' )
        self._base_release.inc = self._base_release.inc + " -I{} -I{} ".format(core_path, hardware_path) 
        # 
        self._base_release.cflags   = self._base_release.cflags + ' -mmcu=atmega328p -w -fno-exceptions -ffunction-sections -fdata-sections -fno-threadsafe-statics -DARDUINO=10604 -DARDUINO_AVR_UNO -DARDUINO_ARCH_AVR'

        self._base_release.asmflags = self._base_release.cflags

        self._base_release.linklibs  = ' -Wl,--start-group -lm -Wl,--end-group'
        self._base_release.linkflags = ' -Wl,--gc-sections'

        self._debug_release.cflags   = self._debug_release.cflags + ' -g -D DEBUG'
        self._debug_release.asmflags = self._debug_release.cflags
           
        self._optimized_release.cflags    = self._optimized_release.cflags + ' -Os -D RELEASE'
        self._optimized_release.asmflags  = self._optimized_release.cflags


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
    def link( self, arguments, inf, local_external_setting, variant ):
        # Run the linker
        base.ToolChain.link(self, arguments, inf, local_external_setting, variant )

        # switch to the build variant output directory
        vardir = '_' + self._bld
        utils.push_dir( vardir )

        # construct objcopy command
        options = '-O ihex -R .eeprom'
        objcpy = '{} {} {} {}'.format(  self._objcpy,
                                        options,
                                        self._final_output_name.replace(".hex",".elf"),
                                        self._final_output_name
                                     )
                                          
        # do the compile
        if ( arguments['-v'] ):
            self._printer.output( objcpy )
        if ( utils.run_shell(self._printer, objcpy) ):
            self._printer.output("=")
            self._printer.output("= Build Failed: Failed to create .HEX file from the .ELF" )
            self._printer.output("=")
            sys.exit(1)

        # Return to project dir
        utils.pop_dir()
        

    #--------------------------------------------------------------------------
    def validate_cc( self ):
        if ( self._env_error != None ):
            exit( "ERROR: The {} environment variable is not set.".format( self._env_error) )
        
        return base.ToolChain.validate_cc(self)
