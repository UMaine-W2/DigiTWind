# Copyright 2023 - Yuksel Rudy Alkarem

import numpy as np
import pandas as pd
import time
import multiprocessing as mp
import os

# Digital Twin Modules
from DigiTWind.nerve import NervePhysical, NerveVirtual
from DigiTWind.GUI.retina import Retina
from DigiTWind.memory import Memory

class Brain:
    def __init__(self, dtw_settings):
        # DigiTWind Settings
        # title and test name
        self.title         = dtw_settings['title']                          # name of the digital twin
        self.test_name     = dtw_settings['test_name']                      # Name of the test
        # time settings
        self.twin_rate     = dtw_settings['time_settings']['twin_rate']     # twin rate (twin frequency)
        self.t_max         = dtw_settings['time_settings']['t_max']         # maximum duration
        # channel information
        self.channel_info  = dtw_settings['channel_info']                   # channels information
        self.channels      = list(self.channel_info.keys())                 # channels
        # DigiTWind modes
        self.physical_env  = dtw_settings['modes']['physical_env']          # flag for the Physical system.
        self.virtual_env   = dtw_settings['modes']['virtual_env']           # flag for the virtual system.
        self.gui           = dtw_settings['modes']['gui']                   # flag for graphical user interface
        # variables
        self.pdata         = None
        self.vdata         = None
        # memory variables
        self.memory        = Memory(self.channels, self.t_max, self.twin_rate)



    def load_pdata(self, filename):
        self.pdata = NervePhysical(filename)

    def preprocess_pdata(self):
        df = self.pdata.get_data()                              # import data
        df = df[self.channels].copy()                           # isolate channels of interest
        df = self.pdata.scale_data(df, self.channel_info, True) # scale channels of interest (and zero drift)
        df = df[df['Time'] <= self.t_max + self.twin_rate]
        time_range = np.arange(0, self.t_max + self.twin_rate, self.twin_rate)
        df_interpolated = pd.DataFrame()
        for channel in self.channels:
            df_interpolated[channel] = np.interp(time_range, df['Time'], df[channel])
        df_interpolated.reset_index(drop=True, inplace=True)
        self.sync_pdata_df = df_interpolated

    def print_sync_pdata(self):
        for i, row in self.sync_pdata_df.iterrows():
            if row['Time'] <= self.t_max:
                row_dict = row.to_dict()
                row_dict['Time'] = row['Time']
                row_dict = {k: float(f"{v:.4f}") if isinstance(v, float) else v for k, v in row_dict.items()}
                print(f"P : {row_dict}")
                # Store physical data in the shared dictionary
                self.memory.shared_pdata[self.memory.shared_ptime.value] = row_dict
                time.sleep(self.twin_rate)
                self.memory.shared_ptime.value += self.twin_rate
            else:
                break

    def physproc1(self, filename):
        self.load_pdata(filename)
        self.preprocess_pdata()
        self.print_sync_pdata()

    def print_sync_vdata(self):
        while self.memory.shared_vtime.value <= self.t_max:
            # Calculate the maximum value calculated in the model and whether it's syncronizable or not
            Tvmax= self.vdata.shared_max_time

            # Check if Physical Mode is on to synchronize with it.
            if self.physical_env:
                synchronizability = Tvmax.value >= self.memory.shared_ptime.value
                self.memory.shared_vtime.value = self.memory.shared_ptime.value
            else:
                synchronizability = True

            if synchronizability:
                # Get all data for the current time
                data = self.vdata.shared_dict[self.memory.shared_vtime.value]
                # Select only the desired channels
                data = {channel: data[channel] for channel in self.channels}
                for channel, info in self.channel_info.items():
                    if not channel == 'Time':
                        Vzdrift = info['Vzdrift']
                        if True:  # hard coded for now to remove zero mean drift
                            data[channel] -= Vzdrift
                row_dict = {k: float(f"{v:.4f}") if isinstance(v, float) else v for k, v in data.items()}
                print(f"V : {row_dict}")
                # Append data to list
                self.memory.vdata_list.append(row_dict)
                # Store virtual data in the shared dictionary
                self.memory.shared_vdata[self.memory.shared_vtime.value] = row_dict
                time.sleep(self.twin_rate)
                self.memory.shared_vtime.value += self.twin_rate

    def virtproc1(self, model_config, turbine_params, turbine_name, controller_params):
        # Create an instance of NerveVirtual
        self.vdata = NerveVirtual(self.twin_rate)

        # Update twin rate in the DISCON file
        self.vdata.update_twin_rate(model_config.param_filename, turbine_params, turbine_name, controller_params)
        clean_variables, of_file = self.vdata.change_model_setup(
            model_config.fastfile,
            model_config.OF_filename,
            model_config.f_list,
            model_config.v_list,
            model_config.des_v_list)

        # Run ZeroMQ (P1) and OpenFAST(P2) in parallel
        p1 = mp.Process(target=self.vdata.run_zmq)
        p2 = mp.Process(target=self.vdata.run_virtual, args=(
            model_config.OF_filename,
            model_config.fastcall,
            model_config.fastfile,
            model_config.lib_name,
            model_config.param_filename))
        p3 = mp.Process(target=self.print_sync_vdata)

        p1.start()
        p2.start()

        # Let the initiation finishes
        time.sleep(5)
        p3.start()

        p1.join()
        p2.join()
        p3.join()

        # Convert list of data points to DataFrame
        df = pd.DataFrame(list(self.memory.vdata_list))  # Convert managed list to ordinary list
        df['Time'] = pd.to_timedelta(df['Time'], unit='S')  # Assuming 'Time' is in seconds
        self.sync_vdata_df = df

        # Restore model setup to clean version
        self.vdata.restore_model_setup(
            model_config.f_list,
            model_config.v_list,
            clean_variables, of_file)

        # Send output files to the designated output folder
        self.vdata.output_manager(
            model_config.OF_filename,
            'output', of_file)

    def realize(self, channels):
        error_dict = {channel: 0 for channel in channels[1:]}  # Initiate error_dict with zeros for all channels
        while self.memory.shared_ptime.value <= self.t_max:
            # Ensure that the current time exists in both shared dictionaries
            if self.memory.shared_ptime.value in self.memory.shared_pdata and self.memory.shared_ptime.value in self.memory.shared_vdata:
                if self.memory.shared_ptime.value == self.memory.shared_vtime.value:
                    pdata_dict = self.memory.shared_pdata[self.memory.shared_ptime.value]
                    vdata_dict = self.memory.shared_vdata[self.memory.shared_ptime.value]

                    # Calculate the absolute error for each channel and add it to the corresponding total error
                    for channel, info in self.channel_info.items():
                        if not channel=='Time': # Skip the first channel
                            if channel in pdata_dict and channel in vdata_dict:
                                pdata = pdata_dict[channel]
                                vdata = vdata_dict[channel]
                                error_dict[channel] = abs(pdata - vdata)
                                self.memory.current_error_dict[channel] = error_dict[channel]
                                self.memory.total_error_dict[channel] += error_dict[channel]
                                tol = info['std'] * info['tol']
                                self.memory.fidelity_test(error_dict[channel], tol, channel)

                # Print the total error for each channel
                for channel, error in error_dict.items():
                    print(f"Current error for {channel}: {error}")

                time.sleep(self.twin_rate)

        # Report Final Fidelity values
        self.memory.report_fidelity()
        # Write mirroring coefficient to an external file
        self.memory.write_mirrcoeff_t(filename="MC_" + self.test_name + ".csv")

    def metrolize(self, filename=None, model_config=None, turbine_params=None,
                  turbine_name=None, controller_params=None):
        if self.physical_env and filename is None:
            raise ValueError("A filename must be provided when running in physical mode.")
        if self.virtual_env and (model_config is None or turbine_params is None or
                                 turbine_name is None or controller_params is None):
            raise ValueError("All virtual parameters must be provided when running in virtual mode.")

        processes = []

        if self.physical_env:
            print('Physical Process Starting Now')
            processes.append(mp.Process(target=self.physproc1, args=[filename]))

        if self.virtual_env:
            processes.append(mp.Process(target=self.virtproc1, args=(
                model_config,
                turbine_params,
                turbine_name,
                controller_params)))

        if self.physical_env and self.virtual_env:
            processes.append(mp.Process(target=self.realize, args=[self.channels]))

        if self.gui:
            processes.append(mp.Process(target=self.visualize))

        for p in processes:
            p.start()

        for p in processes:
            p.join()

    def visualize(self):
        if self.gui:
            # self.memory.shared_pdata = {
            #     0.0:
            #          {'Time': 0.0, 'PtfmTDX': -0.5221, 'PtfmRDY': 0.0101},
            #     1.0:
            #          {'Time': 1.0, 'PtfmTDX': -0.5352, 'PtfmRDY': 0.0105},
            #     2.0:
            #          {'Time': 2.0, 'PtfmTDX': -0.5384, 'PtfmRDY': 0.011},
            #     3.0:
            #          {'Time': 3.0, 'PtfmTDX': -0.5381, 'PtfmRDY': 0.0108},
            #     4.0:
            #          {'Time': 4.0, 'PtfmTDX': -0.5373, 'PtfmRDY': 0.0102},
            #     5.0:
            #          {'Time': 5.0, 'PtfmTDX': -0.5364, 'PtfmRDY': 0.0113},
            #     6.0:
            #          {'Time': 6.0, 'PtfmTDX': -0.536, 'PtfmRDY': 0.0121},
            #     7.0:
            #          {'Time': 7.0, 'PtfmTDX': -0.5341, 'PtfmRDY': 0.0115},
            #     8.0:
            #          {'Time': 8.0, 'PtfmTDX': -0.5325, 'PtfmRDY': 0.0106},
            #     9.0:
            #          {'Time': 9.0, 'PtfmTDX': -0.5285, 'PtfmRDY': 0.01},
            #     10.0:
            #          {'Time': 10.0, 'PtfmTDX': -0.5268, 'PtfmRDY': 0.0105}
            #      }
            # self.memory.shared_vdata = {
            #     0.0:
            #          {'Time': 0.0, 'PtfmTDX': -1.5221, 'PtfmRDY': 1.0101},
            #     1.0:
            #          {'Time': 1.0, 'PtfmTDX': -1.5352, 'PtfmRDY': 1.0105},
            #     2.0:
            #          {'Time': 2.0, 'PtfmTDX': -1.5384, 'PtfmRDY': 1.011},
            #     3.0:
            #          {'Time': 3.0, 'PtfmTDX': -1.5381, 'PtfmRDY': 1.0108},
            #     4.0:
            #          {'Time': 4.0, 'PtfmTDX': -1.5373, 'PtfmRDY': 1.0102},
            #     5.0:
            #          {'Time': 5.0, 'PtfmTDX': -1.5364, 'PtfmRDY': 1.0113},
            #     6.0:
            #          {'Time': 6.0, 'PtfmTDX': -1.536, 'PtfmRDY': 1.0121},
            #     7.0:
            #          {'Time': 7.0, 'PtfmTDX': -1.5341, 'PtfmRDY': 1.0115},
            #     8.0:
            #          {'Time': 8.0, 'PtfmTDX': -1.5325, 'PtfmRDY': 1.0106},
            #     9.0:
            #          {'Time': 9.0, 'PtfmTDX': -1.5285, 'PtfmRDY': 1.01},
            #     10.0:
            #          {'Time': 10.0, 'PtfmTDX': -1.5268, 'PtfmRDY': 1.0105}
            #      }
            app = Retina(self)
            app.run_()

class ModelConfig:
    def __init__(self, fastfile, fastcall, OF_filename, f_list, v_list, des_v_list, lib_name, param_filename):
        self.fastfile = fastfile
        self.fastcall = fastcall
        self.OF_filename = OF_filename
        self.f_list = f_list
        self.v_list = v_list
        self.des_v_list = des_v_list
        self.lib_name = lib_name
        self.param_filename = param_filename
