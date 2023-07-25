"""
----------- P2V_05 --------------
this example synchronizes P2B with V2B and demonstrates DigiTWind's GUI Capabilities and platform visualization (not animated) capabilities
-------------------------------------

In this example:
  - Same as P2V_04 but with additional channels (All 6 DOF)
"""

# Python Modules
import os
from ROSCO_toolbox.inputs.validation import load_rosco_yaml

# Digital Twin Modules
from DigiTWind.brain import Brain, ModelConfig

# CONSTANTS
TITLE         = "DigiTWind"                 # Name of the digital twin
TEST_NAME     = "P2V_05"                    # Name of the test
SCALE         = 70                          # Froude scale of experimental data
TWIN_RATE     = 1.0                         # Twin rate
T_MAX         = 10                          # Total run time
TOL           = 0.00                        # error tolerance (percentage of experimental std)

PHYSICAL_ENV  = True                        # Physical environment mode
VIRTUAL_ENV   = True                        # Virtual environment mode
GUI           = True                        # Graphical User Interface mode


# Physical database name and directory
P_name      = 'test.csv'
this_dir    = os.path.dirname(os.path.abspath(__file__))
P_dir       = os.path.join(os.path.dirname(os.path.dirname(this_dir)),
                            'Test_Cases','Physical')
P_filename  = os.path.join(P_dir,P_name)

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
mesh_file_path   = os.path.join(this_dir, V_filename, 'Hydro', 'wamit_inputs', 'IEA-15-240-RWT.gdf')
fastcall         = os.path.join(this_dir,'../../OpenFAST/install/bin','openfast')
f_list           = ['Fst']
v_list           = ['TMax'] # Should be written exactly as in the OpenFAST input file
des_v_list       = [T_MAX]
# ROSCO DISCON LIBRARY
lib_name         = os.path.join(this_dir,'../../ROSCO/ROSCO/build/libdiscon.so')
param_filename   = os.path.join(V_filename, 'controller', 'DISCON.IN')

# Run Virtual model in parallel with ZMQ
model_config = ModelConfig(fastfile, fastcall, V_filename, f_list, v_list,
    des_v_list, lib_name, param_filename, mesh_file_path)

# Digital Twin settings

dtw_settings = {
    'title'                : TITLE,
    'test_name'            : TEST_NAME,
    'time_settings': {
            'twin_rate'    : TWIN_RATE,
            't_max'        : T_MAX
    },
    'channel_info' : {
        'scale'            : SCALE,
        'TNAME'            : ['Time', 'PtfmTDX', 'PtfmTDY', 'PtfmTDZ', 'PtfmRDX', 'PtfmRDY', 'PtfmRDZ'], # Technical channel name
        'LNAME'            : ['Time', 'Surge', 'Sway', 'Heave', 'Roll', 'Pitch', 'Yaw'],                 # user-friendly channel name
        'UNIT'             : ['s', 'm', 'm', 'm', 'deg', 'deg', 'deg']                                  # channel units
    },
    'modes'         : {
            'physical_env': PHYSICAL_ENV,
            'virtual_env' : VIRTUAL_ENV,
            'gui'         : GUI
    },
    'model_config'        : model_config,
    'tol'                 : TOL
}
dtw = Brain(dtw_settings)
# dtw.visualize()
dtw.metrolize(filename=P_filename,
              turbine_params=turbine_params,
              turbine_name=turbine_name,
              controller_params=controller_params)