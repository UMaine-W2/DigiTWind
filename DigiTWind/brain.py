# Copyright 2023 - Yuksel Rudy Alkarem

import numpy as np
import pandas as pd
import time
import multiprocessing as mp

# Digital Twin Modules
from DigiTWind.nerve import NervePhysical, NerveVirtual

class Brain:
    def __init__(self, twin_rate, TMax, channels):
        self.twin_rate     = twin_rate
        self.TMax          = TMax
        self.channels      = channels
        self.pdata         = None
        self.vdata         = None
        self.sync_pdata_df = None
        self.sync_vdata_df = None
        self.manager       = mp.Manager()  # Create a Manager
        self.vdata_list    = self.manager.list()  # Use the Manager to create the list
        self.real_ptime    = 0.0
        self.real_vtime    = 0.0

    def load_pdata(self, filename):
        self.pdata = NervePhysical(filename)

    def sync_pdata(self):
        df = self.pdata.get_data()
        df = df[self.channels].copy()
        df['Time'] = pd.to_timedelta(df['Time'], unit='S')  # Assuming 'Time' is in seconds
        df.set_index('Time', inplace=True)

        # Resample to your desired frequency, and interpolate to fill NaN values
        new_df = df.resample(f'{self.twin_rate}S').interpolate(method='linear')

        # Trim the dataframe based on the 'Time' column
        new_df = new_df.loc[new_df.index.total_seconds() <= self.TMax]

        self.sync_pdata_df = new_df.reset_index()

    def print_sync_pdata(self):
        for i, row in self.sync_pdata_df.iterrows():
            if row['Time'].total_seconds() <= self.TMax:
                row_dict = row.to_dict()
                row_dict['Time'] = row['Time'].total_seconds()
                row_dict = {k: float(f"{v:.4f}") if isinstance(v, float) else v for k, v in row_dict.items()}
                print(row_dict)
                time.sleep(self.twin_rate)
            else:
                break

    def run_vmodel(self, model_config, turbine_params, turbine_name, controller_params):
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
        df = pd.DataFrame(list(self.vdata_list))  # Convert managed list to ordinary list
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

    def print_sync_vdata(self):
        while self.real_vtime <= self.TMax:
            # Get all data for current time
            data = self.vdata.shared_dict[self.real_vtime]

            # Select only the desired channels
            data = {channel: data[channel] for channel in self.channels}

            row_dict = {k: float(f"{v:.4f}") if isinstance(v, float) else v for k, v in data.items()}
            print(row_dict)

            # Append data to list
            self.vdata_list.append(row_dict)

            time.sleep(self.twin_rate)
            self.real_vtime += self.twin_rate

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
