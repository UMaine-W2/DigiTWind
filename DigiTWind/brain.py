# Copyright 2023 - Yuksel Rudy Alkarem

import numpy as np
import pandas as pd
import time
import multiprocessing as mp

# Digital Twin Modules
from DigiTWind.nerve import NervePhysical, NerveVirtual

class Brain:
    def __init__(self, twin_rate, TMax, channels, p_on, v_on):
        self.twin_rate     = twin_rate
        self.TMax          = TMax
        self.channels      = channels
        self.pdata         = None
        self.vdata         = None
        self.sync_pdata_df = None
        self.sync_vdata_df = None
        self.manager       = mp.Manager()  # Create a Manager
        self.vdata_list    = self.manager.list()  # Use the Manager to create the list
        self.shared_ptime  = self.manager.Value('d', 0.0)
        self.shared_vtime  = self.manager.Value('d', 0.0)
        self.shared_pdata  = self.manager.dict() # Create a shared dictionary for the physical data
        self.shared_vdata  = self.manager.dict() # Create a shared dictionary for the virtual data
        self.physical_on   = p_on # flag for the Physical system.
        self.virtual_on    = v_on # flag for the Virtual system.
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
                print(f"P : {row_dict}")
                # Store physical data in the shared dictionary
                self.shared_pdata[self.shared_ptime.value] = row_dict
                time.sleep(self.twin_rate)
                self.shared_ptime.value += self.twin_rate
            else:
                break

    def physproc1(self, filename):
        self.load_pdata(filename)
        self.sync_pdata()
        self.print_sync_pdata()

    def print_sync_vdata(self):
        while self.shared_vtime.value <= self.TMax:
            # Calculate the maximum value calculated in the model and whether it's syncronizable or not
            Tvmax= self.vdata.shared_max_time

            # Check if Physical Mode is on to synchronize with it.
            if self.physical_on:
                synchronizability = Tvmax.value >= self.shared_ptime.value
                self.shared_vtime.value = self.shared_ptime.value
            else:
                synchronizability = True

            if synchronizability:
                # Get all data for the current time
                data = self.vdata.shared_dict[self.shared_vtime.value]
                # Select only the desired channels
                data = {channel: data[channel] for channel in self.channels}

                row_dict = {k: float(f"{v:.4f}") if isinstance(v, float) else v for k, v in data.items()}
                print(f"V : {row_dict}")
                # Append data to list
                self.vdata_list.append(row_dict)
                # Store virtual data in the shared dictionary
                self.shared_vdata[self.shared_vtime.value] = row_dict
                time.sleep(self.twin_rate)
                self.shared_vtime.value += self.twin_rate

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

    def p2v_metrology(self, filename=None, model_config=None, turbine_params=None,
                      turbine_name=None, controller_params=None):

        if self.physical_on and filename is None:
            raise ValueError("A filename must be provided when running in physical mode.")
        if self.virtual_on and (model_config is None or turbine_params is None or
                                turbine_name is None or controller_params is None):
            raise ValueError("All virtual parameters must be provided when running in virtual mode.")

        processes = []

        if self.physical_on:
            processes.append(mp.Process(target=self.physproc1, args=[filename]))

        if self.virtual_on:
            processes.append(mp.Process(target=self.virtproc1, args=(
                model_config,
                turbine_params,
                turbine_name,
                controller_params)))

        if self.physical_on and self.virtual_on:
            processes.append(mp.Process(target=self.p2v_realization, args=[self.channels]))

        for p in processes:
            p.start()

        for p in processes:
            p.join()

    def p2v_realization(self, channels):
        error_dict = {channel: 0 for channel in channels[1:]}  # Initiate error_dict with zeros for all channels
        total_error_dict = {channel: 0 for channel in channels[1:]}  # Initiate total_error_dict with zeros for all channels
        while self.shared_ptime.value <= self.TMax:
            # Ensure that the current time exists in both shared dictionaries
            if self.shared_ptime.value in self.shared_pdata and self.shared_ptime.value in self.shared_vdata:
                pdata_dict = self.shared_pdata[self.shared_ptime.value]
                vdata_dict = self.shared_vdata[self.shared_ptime.value]

                # Calculate the absolute error for each channel and add it to the corresponding total error
                for channel in channels[1:]:  # Skip the first channel, which is 'Time'
                    if channel in pdata_dict and channel in vdata_dict:
                        error_dict[channel] = abs(pdata_dict[channel] - vdata_dict[channel])
                        total_error_dict[channel] += error_dict[channel]

            # Print the total error for each channel
            for channel, error in error_dict.items():
                print(f"Current error for {channel}: {error}")

            time.sleep(self.twin_rate)

        for channel, total_error in total_error_dict.items():
            print(f"Total error for {channel}: {total_error}")

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
