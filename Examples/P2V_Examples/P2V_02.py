"""
----------- P2V_02 --------------
this example runs the numerical model and prints it on a twin rate frequency
-------------------------------------

In this example:
  - Define a twin_rate
  - Setup numerical Model variables
  - load yaml file
  - Define virtual database name and directory (FAST+ROSCO)
  - Read, update, and write DISCON file with ZMQ_UpdatePeriod = twin_rate
  - Run the virtual model (change settings, runs in parallel with ZMQ, restores)
  - print virtual data at every twin rate.
"""
# Python Modules
import os
from ROSCO_toolbox.inputs.validation import load_rosco_yaml

# Digital Twin Modules
from DigiTWind.brain import Brain, ModelConfig

# Digital Twin settings
twin_rate = 1.0
TMax      = 20
channels  = ['Time', 'PtfmTDX', 'PtfmRDY']

# Numerical Model Setup

# Load yaml file
this_dir           = os.path.dirname(os.path.abspath(__file__))
tune_dir           = os.path.join(this_dir, '../../Tune_Cases')
parameter_filename = os.path.join(tune_dir, 'NREL_FOCAL_V2.yaml')
inps               = load_rosco_yaml(parameter_filename)
path_params        = inps['path_params']
turbine_params     = inps['turbine_params']
controller_params  = inps['controller_params']

# Virtual Models database name and directory
# FAST
fastfile         = path_params['FAST_InputFile']
turbine_name, _  = os.path.splitext(fastfile)
V_filename       = path_params['FAST_directory']
fastcall         = os.path.join(this_dir,'../../OpenFAST/install/bin','openfast')
f_list           = ['Fst']
v_list           = ['TMax']
des_v_list       = [TMax]
# ROSCO DISCON LIBRARY
lib_name         = os.path.join(this_dir,'../../ROSCO/ROSCO/build/libdiscon.so')
param_filename   = os.path.join(V_filename, 'controller', 'DISCON.IN')

# Run Virtual model in parallel with ZMQ
model_config = ModelConfig(fastfile, fastcall, V_filename, f_list, v_list,
    des_v_list, lib_name, param_filename)
dt = Brain(twin_rate, TMax, channels)
dt.run_vmodel(model_config, turbine_params, turbine_name, controller_params)
