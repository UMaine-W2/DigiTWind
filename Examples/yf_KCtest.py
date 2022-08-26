'''
----------- yf_KCtest --------------
Equilibrium Position Test for FOCAL model (load yaml and write DISCON.IN)
[I'm testing StC_Mode=2 here]
-------------------------------------

In this example:
  - Load a default .yaml file
  - Modify .yaml file
  - Save the new .yaml file
  - Load OpenFAST input files
  - Modify OpenFAST input files for writing DISCON.IN file
  - Write DISCON.IN file
  - Revert back to clean input files
  - Modify OpenFAST input files for the simulation Setup
  - Run OpenFAST from ROSCO with StC_Mode=2 [reads K & C values from an external file]
  - Revert back to clean input files

'''
# Python Modules
import os
# ROSCO toolbox modules
from ROSCO_toolbox.utilities import run_openfast, write_DISCON
from ROSCO_toolbox.inputs.validation import load_rosco_yaml
from ROSCO_toolbox import controller as ROSCO_controller
from ROSCO_toolbox import turbine as ROSCO_turbine
from ROSCO_toolbox.ofTools.fast_io.FAST_reader import InputReader_OpenFAST
from ROSCO_toolbox.ofTools.fast_io.FAST_writer import InputWriter_OpenFAST
from ROSCO_toolbox.ofTools.util.FileTools import load_yaml, save_yaml

this_dir = os.path.dirname(os.path.abspath(__file__))
tune_dir = os.path.join(this_dir,'../Tune_Cases')
Test_Name = 'yf_KCtest'
example_out_dir = os.path.join(this_dir,'examples_out')

if not os.path.isdir(example_out_dir):
  os.makedirs(example_out_dir)

# YAML management
old_yaml = 'focal.yaml'
new_yaml = 'focal_OL.yaml'
# Load yaml file
YAML = load_yaml(os.path.join(tune_dir,old_yaml))

# Change yaml file
YAML['controller_params']['StC_Z_filename'] = os.path.abspath(os.path.join(this_dir,'../Tune_Cases/KC_values/KC_test.txt'))
YAML['controller_params']['StC_Mode'] = 2

# save yaml file
save_yaml(tune_dir, new_yaml, YAML)
parameter_filename = os.path.join(tune_dir,new_yaml)
inps = load_rosco_yaml(parameter_filename)
path_params         = inps['path_params']
turbine_params      = inps['turbine_params']
controller_params   = inps['controller_params']

# Instantiate turbine, controller, and file processing classes
turbine         = ROSCO_turbine.Turbine(turbine_params)
controller      = ROSCO_controller.Controller(controller_params)


# OpenFAST input files for Reading & Writing
fastin = InputReader_OpenFAST(FAST_ver='OpenFAST')
fastout = InputWriter_OpenFAST(FAST_ver='OpenFAST')

fastin.FAST_InputFile = path_params['FAST_InputFile']  # FAST input file (ext=.fst)
fastin.FAST_directory = os.path.join(tune_dir,path_params['FAST_directory'])
fastout.FAST_namingOut = fastin.FAST_InputFile[:-4]
fastout.FAST_runDirectory = fastin.FAST_directory

# .fst
fastin.read_MainInput()
# ElastoDyn.dat
fastin.read_ElastoDyn()
# ServoDyn.dat
# fastin.read_ServoDyn()
# HydroDyn.dat
# fastin.read_HydroDyn()

fastout.fst_vt = fastin.fst_vt

# Back up clean variables
CompAero_Clean = fastin.fst_vt['Fst']['CompAero']
CompInflow_Clean = fastin.fst_vt['Fst']['CompInflow']
InflowFile_Clean = fastin.fst_vt['Fst']['InflowFile']
AeroFile_Clean = fastin.fst_vt['Fst']['AeroFile']
GBRatio_Clean = fastin.fst_vt['ElastoDyn']['GBRatio']
TipRad_Clean = fastin.fst_vt['ElastoDyn']['TipRad']
HubRad_Clean = fastin.fst_vt['ElastoDyn']['HubRad']
GenIner_Clean = fastin.fst_vt['ElastoDyn']['GenIner']
# Simulation Setup
fastout.fst_vt['Fst']['CompAero'] = 2
fastout.fst_vt['Fst']['CompInflow'] = 1
fastout.fst_vt['Fst']['InflowFile'] = 'dummy_InflowFile.dat'
fastout.fst_vt['Fst']['AeroFile'] = 'dummy_AeroDyn15.dat'
fastout.fst_vt['ElastoDyn']['GBRatio'] = 1.0
fastout.fst_vt['ElastoDyn']['TipRad'] = 120
fastout.fst_vt['ElastoDyn']['HubRad'] = 3.0
fastout.fst_vt['ElastoDyn']['GenIner'] = 8.00865E+06
# Applying changes to input files
fastout.write_MainInput()
fastout.write_ElastoDyn()

# Load turbine data from OpenFAST and rotor performance text file
turbine.load_from_fast(
    path_params['FAST_InputFile'],
    os.path.join(tune_dir,path_params['FAST_directory']),
    rot_source='txt',txt_filename=os.path.join(tune_dir,path_params['rotor_performance_filename'])
    )


# Rewriting clean version
fastout.fst_vt['Fst']['CompAero'] = CompAero_Clean
fastout.fst_vt['Fst']['CompInflow'] = CompInflow_Clean
fastout.fst_vt['Fst']['InflowFile'] = InflowFile_Clean
fastout.fst_vt['Fst']['AeroFile'] = AeroFile_Clean
fastout.fst_vt['ElastoDyn']['GBRatio'] = GBRatio_Clean
fastout.fst_vt['ElastoDyn']['TipRad'] = TipRad_Clean
fastout.fst_vt['ElastoDyn']['HubRad'] = HubRad_Clean
fastout.fst_vt['ElastoDyn']['GenIner'] = GenIner_Clean
fastout.write_MainInput()
fastout.write_ElastoDyn()

# Tune controller
controller.tune_controller(turbine)

# Write parameter input file
param_file = os.path.join(this_dir,path_params['FAST_directory'],'controller','DISCON.IN')
write_DISCON(turbine,controller,param_file=param_file, txt_filename=os.path.join(tune_dir,path_params['rotor_performance_filename']))


# OpenFAST input files for Reading & Writing
fastin = InputReader_OpenFAST(FAST_ver='OpenFAST')
fastout = InputWriter_OpenFAST(FAST_ver='OpenFAST')

fastin.FAST_InputFile = path_params['FAST_InputFile']  # FAST input file (ext=.fst)
fastin.FAST_directory = os.path.join(tune_dir,path_params['FAST_directory'])
fastout.FAST_namingOut = fastin.FAST_InputFile[:-4]
fastout.FAST_runDirectory = fastin.FAST_directory

# .fst
fastin.read_MainInput()
# ElastoDyn.dat
# fastin.read_ElastoDyn()
# ServoDyn.dat
# fastin.read_ServoDyn()
# HydroDyn.dat
# fastin.read_HydroDyn()

fastout.fst_vt = fastin.fst_vt

# Back up clean variables
TMax_Clean = fastin.fst_vt['Fst']['TMax']

# Simulation Setup
fastout.fst_vt['Fst']['TMax'] = 100.0

# Applying changes to input files
fastout.write_MainInput()

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
fastout.fst_vt['Fst']['TMax'] = TMax_Clean
fastout.write_MainInput()

# Moving output files to LC output directory (supports: .out, .outb, .MD.out)
example_out_dir_LC = os.path.join(example_out_dir,Test_Name)

if not os.path.isdir(example_out_dir_LC):
  os.makedirs(example_out_dir_LC)

outname = fastout.FAST_namingOut + '.out'
outbname = fastout.FAST_namingOut + '.outb'
MDoutname = fastout.FAST_namingOut + '.MD.out'
if os.path.isfile(os.path.join(fastin.FAST_directory,outname)):
  os.rename(os.path.join(fastin.FAST_directory,outname), os.path.join(example_out_dir_LC,outname))
#
if os.path.isfile(os.path.join(fastin.FAST_directory,outbname)):
  os.rename(os.path.join(fastin.FAST_directory,outbname), os.path.join(example_out_dir_LC,outbname))

if os.path.isfile(os.path.join(fastin.FAST_directory,MDoutname)):
  os.rename(os.path.join(fastin.FAST_directory,MDoutname), os.path.join(example_out_dir_LC,MDoutname))
