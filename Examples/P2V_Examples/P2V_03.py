"""
----------- P2V_03 --------------
this example synchronizes P2B with V2B
-------------------------------------

In this example:
  - Provide digital twin settings
  - Define physical database name and directory
  - Setup numerical Model variables
  - load yaml file
  - Define virtual database name and directory (FAST+ROSCO)
  - Run P2V metrology with both physical and virtual mode turned on
  - Run the virtual model (change settings, runs in parallel with ZMQ, restores)
  - Compare with physical data and print local errors at every twin rate and global error in the end.
"""

# Python Modules
import os
from ROSCO_toolbox.inputs.validation import load_rosco_yaml

# Digital Twin Modules
from DigiTWind.brain import Brain, ModelConfig

# CONSTANTS
TITLE         = "DigiTWind"                 # Name of the digital twin
TEST_NAME     = "P2V_03"                    # Name of the test
SCALE         = 70                          # Froude scale of experimental data
TWIN_RATE     = 1.0                         # Twin rate
T_MAX         = 100                         # Total run time
# Channel 1
CH1NAME = "surge"
CH1UNIT = "m"
CH1PZDRFT = 0.00                            # Physical mean drift in Surge displacement
CH1VZDRFT = 0.00                            # Virtual mean drift in Surge displacement
CH1_STD = 1.4279                            # experimental standard deviation of surge displacement
CH1_TOL = 0.10                              # Surge displacement error tolerance (percentage of experimental std)
# Channel 2
CH2NAME = "pitch"
CH2UNIT = "deg"
CH2PZDRFT = 0.00                            # Physical mean drift in Pitch displacement
CH2VZDRFT = 0.00                            # Virtual mean drift in Pitch displacement
CH2_STD = 0.4335                            # experimental standard deviation of pitch displacement
CH2_TOL = 0.10                              # Pitch displacement error tolerance (percentage of experimental std)

PHYSICAL_ENV  = True                        # Physical environment mode
VIRTUAL_ENV   = True                        # Virtual environment mode
GUI           = False                       # Graphical User Interface mode

# Digital Twin settings


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

dtw_settings = {
    'title'        : TITLE,
    'test_name'    : TEST_NAME,
    'time_settings': {
            'twin_rate': TWIN_RATE,
            't_max'    : T_MAX
    },
    'channel_info': {
        'Time': {'unit': 's', 'scale': SCALE},
        'PtfmTDX': {'name': CH1NAME, 'unit': CH1UNIT, 'scale': SCALE, 'Pzdrift': CH1PZDRFT, 'Vzdrift': CH1VZDRFT,
                    'std': CH1_STD, 'tol': CH1_TOL},
        'PtfmRDY': {'name': CH2NAME, 'unit': CH2UNIT, 'scale': SCALE, 'Pzdrift': CH2PZDRFT, 'Vzdrift': CH2VZDRFT,
                    'std': CH2_STD, 'tol': CH2_TOL},
    },
    'modes': {
            'physical_env': PHYSICAL_ENV,
            'virtual_env' : VIRTUAL_ENV,
            'gui'         : GUI
    },
    'model_config': model_config
}

dtw = Brain(dtw_settings)
dtw.metrolize(filename=P_filename,
              turbine_params=turbine_params,
              turbine_name=turbine_name,
              controller_params=controller_params)