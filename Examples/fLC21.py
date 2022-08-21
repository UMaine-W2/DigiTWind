'''
----------- fLC2.1 --------------
Surge Free Decay Test for FOCAL model
-------------------------------------

In this example:
  - Load OpenFAST input files
  - Modify OpenFAST input files for the simulation setup
  - Write new OpenFAST input files
  - Rewrite original input files
  - Move output files into their corresponding output directory

'''
# Python Modules
import os
# ROSCO toolbox modules
from ROSCO_toolbox.utilities import run_openfast
from ROSCO_toolbox.ofTools.fast_io.FAST_reader import InputReader_OpenFAST
from ROSCO_toolbox.ofTools.fast_io.FAST_writer import InputWriter_OpenFAST

this_dir = os.path.dirname(os.path.abspath(__file__))
Test_Name = 'fLC21'
example_out_dir = os.path.join(this_dir,'examples_out')

if not os.path.isdir(example_out_dir):
  os.makedirs(example_out_dir)

# OpenFAST input files for Reading & Writing
fastin = InputReader_OpenFAST(FAST_ver='OpenFAST')
fastout = InputWriter_OpenFAST(FAST_ver='OpenFAST')

fastin.FAST_InputFile = 'DT1.fst'  # FAST input file (ext=.fst)
fastin.FAST_directory = os.path.join(this_dir,'../Test_Cases/FOCAL')
fastout.FAST_namingOut = fastin.FAST_InputFile[:-4]
fastout.FAST_runDirectory = fastin.FAST_directory

# .fst
fastin.read_MainInput()
# ElastoDyn.dat
fastin.read_ElastoDyn()
# ServoDyn.dat
fastin.read_ServoDyn()
# HydroDyn.dat
fastin.read_HydroDyn()

fastout.fst_vt = fastin.fst_vt

# Back up clean variables
PtfmSurge_Clean = fastin.fst_vt['ElastoDyn']['PtfmSurge']
# Simulation Setup
fastout.fst_vt['ElastoDyn']['PtfmSurge'] = 12.25
# Applying changes to input files
fastout.write_ElastoDyn()

# Run OpenFAST
# --- May need to change fastcall if you use a non-standard command to call openfast
fastcall = os.path.join(this_dir,'../OpenFAST/install/bin','openfast')
run_openfast(
  os.path.join(this_dir,fastin.FAST_directory),
  fastcall=fastcall,
  fastfile=fastin.FAST_InputFile,
  chdir=True
  )

# Rewriting clean version
fastout.fst_vt['ElastoDyn']['PtfmSurge'] = PtfmSurge_Clean
fastout.write_ElastoDyn()

# Moving output files to LC output directory (supports: .out, .outb, .MD.out)
example_out_dir_LC = os.path.join(example_out_dir,Test_Name)

if not os.path.isdir(example_out_dir_LC):
  os.makedirs(example_out_dir_LC)

outname = fastout.FAST_namingOut + '.out'
outbname = fastout.FAST_namingOut + '.outb'
MDoutname = fastout.FAST_namingOut + '.MD.out'
if os.path.isfile(os.path.join(fastin.FAST_directory,outname)):
  os.rename(os.path.join(fastin.FAST_directory,outname), os.path.join(example_out_dir_LC,outname))

if os.path.isfile(os.path.join(fastin.FAST_directory,outbname)):
  os.rename(os.path.join(fastin.FAST_directory,outbname), os.path.join(example_out_dir_LC,outbname))

if os.path.isfile(os.path.join(fastin.FAST_directory,MDoutname)):
  os.rename(os.path.join(fastin.FAST_directory,MDoutname), os.path.join(example_out_dir_LC,MDoutname))