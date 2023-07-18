"""
----------- SA --------------
Synchronize-Acquire (SA) - Fidelity Test
-------------------------------------

In this example:
  - Assessing the fidelity of the SA twinning cycle (technically it is not a twinning cycle yet since it does not twin yet)
"""

# Python Modules
import os
from ROSCO_toolbox.inputs.validation import load_rosco_yaml
from ROSCO_toolbox.ofTools.fast_io.FAST_reader import InputReader_OpenFAST
# Digital Twin Modules
from DigiTWind.brain import Brain, ModelConfig
from DigiTWind.nerve import NerveVirtual
# Looping over tolerances
TOLS = [i/10 for i in range(1, 2)]

for tol in TOLS:
    # CONSTANTS
    TITLE         = "DigiTWind"                 # Name of the digital twin
    TEST_NAME     = f"SA_{tol}"                 # Name of the test
    SCALE         = 70                          # Froude scale of experimental data
    TWIN_RATE     = 1.0                         # Twin rate
    T_MAX         = 1000                        # Total run time
    WAVE_MODE     = 5                           # Externally generated wave-elevation time series
    WVKINFILE     = 'test_01'                   # Root name of externally generated wave data file
    WAVEDT        = 0.1                         # Time step for incident wave calculations
    WAVETMAX      = T_MAX + 1                   # Analysis time for incident wave calculations (WAVETMAX > T_MAX, when WAVE_MODE=5)
    # Channel 1
    CH1NAME       = "surge"
    CH1UNIT       = "m"
    CH1PZDRFT     = 0.00                        # Physical mean drift in Surge displacement
    CH1VZDRFT     = 0.00                        # Virtual mean drift in Surge displacement
    CH1_STD       = 1.4279                      # experimental standard deviation of surge displacement
    CH1_TOL       = tol                         # Surge displacement error tolerance (percentage of experimental std)
    # Channel 2
    CH2NAME       = "pitch"
    CH2UNIT       = "deg"
    CH2PZDRFT     = 0.00                        # Physical mean drift in Pitch displacement
    CH2VZDRFT     = 0.00                        # Virtual mean drift in Pitch displacement
    CH2_STD       = 0.4335                      # experimental standard deviation of pitch displacement
    CH2_TOL       = tol                         # Pitch displacement error tolerance (percentage of experimental std)
    PHYSICAL_ENV  = True                       # Physical environment mode
    VIRTUAL_ENV   = True                        # Virtual environment mode
    GUI           = True                        # Graphical User Interface mode

    # Digital Twin settings

    dtw_settings = {
        'title'        : TITLE,
        'test_name'    : TEST_NAME,
        'time_settings': {
                'twin_rate': TWIN_RATE,
                't_max'    : T_MAX
        },
        'channel_info': {
                'Time'   : {'unit': 's', 'scale': SCALE},
                'PtfmTDX': {'name': CH1NAME, 'unit': CH1UNIT, 'scale': SCALE, 'Pzdrift': CH1PZDRFT, 'Vzdrift': CH1VZDRFT, 'std': CH1_STD, 'tol': CH1_TOL},
                'PtfmRDY': {'name': CH2NAME, 'unit': CH2UNIT, 'scale': SCALE, 'Pzdrift': CH2PZDRFT, 'Vzdrift': CH2VZDRFT, 'std': CH2_STD, 'tol': CH2_TOL},
        },
        'modes': {
                'physical_env': PHYSICAL_ENV,
                'virtual_env' : VIRTUAL_ENV,
                'gui'         : GUI
        }
    }

    # Physical database name and directory
    P_name      = 'test_01.csv'
    this_dir    = os.path.dirname(os.path.abspath(__file__))
    P_dir       = os.path.join(os.path.dirname(os.path.dirname(this_dir)),
                                'Test_Cases','Physical')
    P_filename  = os.path.join(P_dir,P_name)

    # Numerical Model Setup

    # Load yaml file
    this_dir           = os.path.dirname(os.path.abspath(__file__))
    tune_dir           = os.path.join(this_dir, '../../Tune_Cases')
    parameter_filename = os.path.join(tune_dir, 'NREL_FOCAL_V2_SA.yaml')
    inps               = load_rosco_yaml(parameter_filename)
    path_params        = inps['path_params']
    turbine_params     = inps['turbine_params']
    controller_params  = inps['controller_params']

    # Virtual Models database name and directory
    # FAST
    fastfile         = path_params['FAST_InputFile']
    turbine_name, _  = os.path.splitext(fastfile)
    V_filename       = os.path.abspath(path_params['FAST_directory'])
    fastcall         = os.path.join(this_dir,'../../OpenFAST/install/bin','openfast')
    f_list           = ['Fst', 'HydroDyn', 'HydroDyn', 'HydroDyn', 'HydroDyn']
    v_list           = ['TMax', 'WaveMod', 'WaveTMax', 'WaveDT', 'WvKinFile'] # Should be written exactly as in the OpenFAST input file
    des_v_list       = [T_MAX, WAVE_MODE, WAVETMAX, WAVEDT, WVKINFILE]
    # ROSCO DISCON LIBRARY
    lib_name         = os.path.join(this_dir,'../../ROSCO/ROSCO/build/libdiscon.so')
    param_filename   = os.path.join(V_filename, 'controller', 'DISCON.IN')

    # Run Virtual model in parallel with ZMQ
    model_config = ModelConfig(fastfile, fastcall, V_filename, f_list, v_list,
        des_v_list, lib_name, param_filename)

    dtw = Brain(dtw_settings)
    dtw.metrolize(filename=P_filename,
                  model_config=model_config,
                  turbine_params=turbine_params,
                  turbine_name=turbine_name,
                  controller_params=controller_params)