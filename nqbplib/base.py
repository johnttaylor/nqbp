"""Base toolchain functions and classes"""

#
import logging
import time
import os
import shutil
import sys
import subprocess

#
import utils

# Globals
from my_globals import NQBP_WORK_ROOT
from my_globals import NQBP_PKG_ROOT
from my_globals import NQBP_TEMP_EXT
from my_globals import NQBP_VERSION
from my_globals import NQBP_PRJ_DIR
from my_globals import NQBP_WRKPKGS_DIRNAME
from my_globals import NQBP_PUBLICAPI_DIRNAME


# Structure for holding build-variant specific options
class BuildValues:
    def __init__(self):
        self.inc        = ''
        self.asminc     = ''
        self.cflags     = ''
        self.cppflags   = ''
        self.asmflags   = ''
        self.linkflags  = ''
        self.linklibs   = ''
        self.linkscript = ''
        self.firstobjs  = ''

    def append(self,src):
        self.inc        += ' ' + src.inc        
        self.asminc     += ' ' + src.asminc           
        self.cflags     += ' ' + src.cflags           
        self.cppflags   += ' ' + src.cppflags         
        self.asmflags   += ' ' + src.asmflags         
        self.linkflags  += ' ' + src.linkflags        
        self.linklibs   += ' ' + src.linklibs 
        self.linkscript += ' ' + src.linkscript 
        self.firstobjs  += ' ' + src.firstobjs 
  
        
    def copy(self):
        new = BuildValues()
        new.inc        = self.inc        
        new.asminc     = self.asminc           
        new.cflags     = self.cflags           
        new.cppflags   = self.cppflags         
        new.asmflags   = self.asmflags         
        new.linkflags  = self.linkflags        
        new.linklibs   = self.linklibs 
        new.linkscript = self.linkscript 
        new.firstobjs  = self.firstobjs 
       
        return new
            

#==============================================================================
class ToolChain:
    """ Base ToolChain Class"""

    #--------------------------------------------------------------------------
    def __init__( self, exename, prjdir, build_variants, default_variant ):
        
        # Housekeeping -->set some global vars    
        NQBP_PRJ_DIR( prjdir )
        
        # Private members
        self._bld_variants    = build_variants
        self._build_time_utc  = int(time.time())
        self._cflag_symdef    = '-D'
        self._asmflag_symdef  = '-D'
        
        # Tools
        self._ccname   = 'Generic GCC'
        self._cc       = 'gcc'  
        self._ld       = 'gcc'  
        self._asm      = 'as'   
        self._ar       = 'ar'   
        self._objcpy   = 'objcpy'
        
        self._obj_ext  = 'o'    
        self._asm_ext  = 's'    
        
        self._echo_cc  = True 
        self._echo_asm = True
        
        self._validate_cc_options = '-v'
        
        self._clean_list     = ['o', 'lst', 'map', 'obj', 'idb', 'pdb', 'out', 'pyc', NQBP_TEMP_EXT(), 'gcda', 'gcov', 'gcno' ]
        self._clean_pkg_dirs = [ 'src' ]
        self._clean_ext_dirs = [ NQBP_WRKPKGS_DIRNAME() ]
 
        self._ar_library_name = 'library.a'
        self._ar_options      = 'rc ' + self._ar_library_name
        
        self._link_lib_prefix       = ''
        self._linker_libgroup_start = '-Wl,--start-group'
        self._linker_libgroup_end   = '-Wl,--end-group'
        
        self._final_output_name = exename
        self._link_output       = '-o ' + exename
        
        
        #
        # Build Config/Variant: "release"
        #
        
        # Common/base options, flags, etc.
        # Notes:
        #   o Order of the header file include path should be in the 
        #     following order (i.e. first directory searched)
        #       - Current directory
        #       - Package source directory
        #       - Project directory
        #       - Workspace Public Include directory
        #
        self._base_release = BuildValues()
        self._base_release.inc       = '-I. -I{}{}src  -I{} -I{}{}{}{}src'.format(NQBP_PKG_ROOT(),os.sep, prjdir, NQBP_WORK_ROOT(),os.sep,NQBP_PUBLICAPI_DIRNAME(),os.sep  )
        self._base_release.asminc    = self._base_release.inc
        self._base_release.cflags    = '-c -DBUILD_TIME_UTC={:d} '.format(self._build_time_utc)
        #self._base_release.linklibs  = '-L lib -Wl,-lstdc++'
        self._base_release.linklibs  = '-Wl,-lstdc++'
        
        # Optimized options, flags, etc.
        self._optimized_release = BuildValues()
        
        # Debug options, flags, etc.
        self._debug_release = BuildValues()
        self._debug_release.cflags = '-g'
        

        # Update dictionary of build variants
        self._bld = default_variant
        self._bld_variants[self._bld]['base']      = self._base_release
        self._bld_variants[self._bld]['optimized'] = self._optimized_release
        self._bld_variants[self._bld]['debug']     = self._debug_release
 
        
    
    #--------------------------------------------------------------------------
    def get_default_variant(self):
        return self._bld
        
        
    #--------------------------------------------------------------------------
    def list_variants(self):
        utils.output( 'Available Build Configurations/Variants:' )
        for key in self._bld_variants.keys():
            marker = ' *' if key == self._bld else ''
            utils.output( '  {}{}'.format(key,marker) )
           
        
    
    #--------------------------------------------------------------------------
    def clean(self, pkg, ext, silent=False):
        if ( pkg == True ):
            if ( not silent ):
                utils.output( "= Cleaning Project and local Package derived objects..." )
            utils.debug( '# Cleaning file extensions: {}'.format( self._clean_list ) )
            utils.del_files_by_ext( NQBP_PRJ_DIR(), self._clean_list )

            utils.debug( '# Cleaning directories: {}'.format( self._clean_pkg_dirs ) )
            for d in self._clean_pkg_dirs:
                if ( os.path.exists(d) ):
                    shutil.rmtree( d, True )

            # remove output/build variant directory
            vardir = '_' + self._bld
            if ( os.path.exists(vardir) ):
                shutil.rmtree( vardir, True )
                            
        if ( ext == True ):
            if ( not silent ):
                utils.output( "= Cleaning External Package derived objects..." )
            utils.debug( '# Cleaning directories: {}'.format( self._clean_ext_dirs ) )
            for d in self._clean_ext_dirs:
                if ( os.path.exists(d) ):
                    shutil.rmtree( d, True )
 
    #--------------------------------------------------------------------------
    def clean_all( self, arguments, silent=False ):            
        for b in self.get_variants():
            if ( not silent ):
                utils.output( "=====================" )
                utils.output( "= Build Variant: " + b )
            self.pre_build( b, arguments )
            self.clean(True,True,silent)
    

    #--------------------------------------------------------------------------
    def get_final_output_name(self):
        return self._final_output_name
                                                                             
    #--------------------------------------------------------------------------
    def get_build_time(self):
        return self._build_time_utc
        
    #--------------------------------------------------------------------------
    def get_build_variant(self):
        return self._bld
    
    #--------------------------------------------------------------------------
    def get_variants(self):
        return self._bld_variants.keys()
            
    #--------------------------------------------------------------------------
    def get_ccname(self):
        return self._ccname
    
    #--------------------------------------------------------------------------
    def get_asm_extensions(self):
        extlist = [ self._asm_ext ]
        return extlist
        
    #--------------------------------------------------------------------------
    def pre_build(self, bld_var, arguments ):
        utils.debug( '# ENTER: base.ToolChain.pre_build' )
        
        # Select/set build variant
        self._bld = bld_var
        if ( not self._bld_variants.has_key(bld_var) ):
            utils.output( 'ERROR: Invalid variant ({}) selected'.format( bld_var ) )
            sys.exit(1)
            
        utils.debug( '# Build Variant "{}" selected'.format( self._bld ) )
        if ( arguments['--debug'] ):
            self._dump_variants( self._bld_variants )
                      
        # Construct build options
        null           = BuildValues()
        bld            = self._bld_variants[self._bld] 
        base           = bld.get('base', self._base_release ).copy() # default to the release 'base' if not defined
        base.cflags   += " {}BUILD_VARIANT_{} ".format(self._cflag_symdef,  self._bld.upper());
        base.asmflags += " {}BUILD_VARIANT_{} ".format(self._asmflag_symdef,self._bld.upper());
        self._all_opts = base
        self._all_opts.append( bld.get('user_base', null ) )
       
        
        if ( arguments['-g'] ):
            self._all_opts.append( bld.get('debug', self._debug_release ) )
            self._all_opts.append( bld.get('user_debug', null ) )
        else:
            self._all_opts.append( bld.get('optimized', self._optimized_release ) )
            self._all_opts.append( bld.get('user_optimized', null ) )
            

    #--------------------------------------------------------------------------
    def ar( self, arguments ):
        # NOTE: Assumes archive is to be built in the current working dir
        utils.output("=" )
        utils.output("= Archiving: {}".format( self._ar_library_name) )
        
        # remove existing archive
        utils.delete_file( self._ar_library_name )
        
        # Get all object files
        objs = utils.dir_list_filter_by_ext( ".", [self._obj_ext] )
       
        # build archive string
        cmd = self._ar + ' ' + self._ar_options
        for o in objs:
            cmd = cmd + ' ' + o
            
        # run command            
        if ( arguments['-v'] ):
            utils.output( cmd )
        if (utils.run_shell(cmd) ):
            utils.output("=")
            utils.output("= Build Failed: archiver/libririan error")
            utils.output("=")
            sys.exit(1)
        
                   
    #--------------------------------------------------------------------------
    def validate_cc( self ):
        cc = self._cc + ' ' + self._validate_cc_options
        p  = subprocess.Popen( cc, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        r  = p.communicate()
        if ( p.returncode ):
            utils.output( "ERROR: Cannot validate toolchain ({}) - check your path/environment variable(s)".format( self._ccname ) )
            sys.exit(1)
      
        return r
              
    #--------------------------------------------------------------------------
    def cc( self, arguments, fullname ):
    
        # construct compiler/assembler command
        cc = '{} {} {}'.format( self._cc,
                                self._all_opts.cflags,
                                self._all_opts.inc
                              )
        if ( fullname.endswith('.c') ):
            pass
        elif ( fullname.endswith('.cpp') ):
            cc += ' ' + self._all_opts.cppflags
        elif ( fullname.endswith(self._asm_ext) ):
            cc = '{} {} {}'.format( self._asm,
                                    self._all_opts.asmflags,
                                    self._all_opts.asminc
                                  )
        else:
            utils.output( "ERROR: No rule to compile the file: {}".format( os.path.basename(fullname) ) )
            sys.exit(1)

        # ensure correct directory seperator                                
        full_fname = utils.standardize_dir_sep( fullname )

        cc += ' ' + full_fname
        
        # Output Progress...
        if ( self._echo_cc ):
            utils.output("= Compiling: " + os.path.basename(fullname) )
        if ( arguments['-v'] ):
            utils.output( cc )
        
        # do the compile
        if ( utils.run_shell(cc) ):
            utils.output("=")
            utils.output("= Build Failed: compiler error")
            utils.output("=")
            sys.exit(1)



    #--------------------------------------------------------------------------
    def link( self, arguments, inf, local_external_setting, variant ):

        # Output Progress...
        utils.output( "=====================" )
        utils.output("= Linking..." )

        # create build variant output
        vardir = '_' + self._bld
        utils.create_subdirectory( '.', vardir )
        utils.push_dir( vardir )
        
        # Set my command options to construct an 'all' libdirs list
        libdirs = []
        myargs  = { '-p':False, '-x':False, '-b':arguments['-b'] }
        utils.create_working_libdirs( inf, myargs, libdirs, local_external_setting, variant )  

        # construct link command
        libs = self._build_library_list( libdirs )
        ld = '{} {} {} {} {} {} {} {} {} {}'.format( 
                                            self._ld,
                                            self._link_output,
                                            self._all_opts.firstobjs,
                                            self._build_prjobjs_list(),
                                            self._all_opts.linkflags,
                                            self._all_opts.linkscript,
                                            self._linker_libgroup_start,
                                            libs,
                                            self._linker_libgroup_end,
                                            self._all_opts.linklibs
                                            )
                                          
        # do the compile
        if ( arguments['-v'] ):
            utils.output( ld )
        if ( utils.run_shell(ld) ):
            utils.output("=")
            utils.output("= Build Failed: linker error")
            utils.output("=")
            sys.exit(1)

        # Return to project dir
        utils.pop_dir()
        
        
    #==========================================================================
    # Private Methods
    #==========================================================================
    
    #--------------------------------------------------------------------------
    def _build_prjobjs_list( self ):
        list = utils.dir_list_filter_by_ext( '..' + os.sep, [self._obj_ext] )
        path = ''
        for i in list:
            path += ' ..' + os.sep + i
        
        return path
        
        
    #--------------------------------------------------------------------------
    def _build_library_list( self, libs ):
        result = ''
        for pair in libs:
            l,f  = pair
            
            path = '..' + os.sep
            if ( f == 'xpkg' ):
                path += NQBP_WRKPKGS_DIRNAME() + os.sep
                
            lname   = path + l + os.sep + self._ar_library_name    
            result += self._link_lib_prefix + lname + ' '
            
        return result
                  
        
    #--------------------------------------------------------------------------
    def _dump_variants( self, bld_variants ):
        utils.debug( '# Build Variants Options' )
        for k,v in bld_variants.items():
            utils.debug( '#  VARIANT: ' + k )
            for sk,sv in v.items():
                if ( sk != 'nop' ):
                    utils.debug( '#    Options: '      + sk )
                    utils.debug( '#      inc:        ' + sv.inc )
                    utils.debug( '#      asminc:     ' + sv.asminc  )
                    utils.debug( '#      cflags:     ' + sv.cflags  )
                    utils.debug( '#      cppflags:   ' + sv.cppflags )
                    utils.debug( '#      asmflags:   ' + sv.asmflags )
                    utils.debug( '#      linkflags:  ' + sv.linkflags )
                    utils.debug( '#      linklibs:   ' + sv.linklibs )
                    utils.debug( '#      firstobjs:  ' + sv.firstobjs )
                    utils.debug( '#      linkscript: ' + sv.linkscript )
  
                                                                         