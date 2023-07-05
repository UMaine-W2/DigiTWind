# Copyright 2023 - Yuksel Rudy Alkarem

import numpy as np
import pandas as pd
import time
import multiprocessing as mp
import os

# Digital Twin Modules
from DigiTWind.nerve import NervePhysical, NerveVirtual

class Brain:
    def __init__(self, time_settings, channel_info, modes):
        # DigiTWind Settings
        self.twin_rate     = time_settings['twin_rate']
        self.TMax          = time_settings['TMax']
        self.channel_info  = channel_info
        self.channels      = list(channel_info.keys())
        self.physical_on   = modes['p_on'] # flag for the Physical system.
        self.virtual_on    = modes['v_on'] # flag for the Virtual system.
        # physical and virtual variables
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
        # Fidelity Testing
        self.mirrcount    = {channel: 0.0 for channel in self.channels} # Mirroring count for fidelity testing
        self.mirrcoeff    = {channel: 0.0 for channel in self.channels} # Mirroring coefficient for fidelity testing
        self.mirrcoeff_t = {channel: [] for channel in self.channels[1:]}   # Mirroring coefficient as a function of time


    def load_pdata(self, filename):
        self.pdata = NervePhysical(filename)

    def preprocess_pdata(self):
        df = self.pdata.get_data()                              # import data
        df = df[self.channels].copy()                           # isolate channels of interest
        df = self.pdata.scale_data(df, self.channel_info, True) # scale channels of interest (and zero drift)
        df = df[df['Time'] <= self.TMax + self.twin_rate]
        time_range = np.arange(0, self.TMax + self.twin_rate, self.twin_rate)
        df_interpolated = pd.DataFrame()
        for channel in self.channels:
            df_interpolated[channel] = np.interp(time_range, df['Time'], df[channel])
        df_interpolated.reset_index(drop=True, inplace=True)
        self.sync_pdata_df = df_interpolated

    def print_sync_pdata(self):
        for i, row in self.sync_pdata_df.iterrows():
            if row['Time'] <= self.TMax:
                row_dict = row.to_dict()
                row_dict['Time'] = row['Time']
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
        self.preprocess_pdata()
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
                for channel, info in self.channel_info.items():
                    if not channel == 'Time':
                        Vzdrift = info['Vzdrift']
                        if True:  # hard coded for now to remove zero mean drift
                            data[channel] -= Vzdrift
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

    def p2v_metrolize(self, filename=None, model_config=None, turbine_params=None,
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
            processes.append(mp.Process(target=self.p2v_realize, args=[self.channels]))

        for p in processes:
            p.start()

        for p in processes:
            p.join()

    def p2v_realize(self, channels):
        error_dict = {channel: 0 for channel in channels[1:]}  # Initiate error_dict with zeros for all channels
        total_error_dict = {channel: 0 for channel in channels[1:]}  # Initiate total_error_dict with zeros for all channels
        while self.shared_ptime.value <= self.TMax:
            # Ensure that the current time exists in both shared dictionaries
            if self.shared_ptime.value in self.shared_pdata and self.shared_ptime.value in self.shared_vdata:
                if self.shared_ptime.value == self.shared_vtime.value:
                    pdata_dict = self.shared_pdata[self.shared_ptime.value]
                    vdata_dict = self.shared_vdata[self.shared_ptime.value]

                    # Calculate the absolute error for each channel and add it to the corresponding total error
                    for channel, info in self.channel_info.items():
                        if not channel=='Time': # Skip the first channel
                            if channel in pdata_dict and channel in vdata_dict:
                                pdata = pdata_dict[channel]
                                vdata = vdata_dict[channel]
                                error_dict[channel] = abs(pdata - vdata)
                                total_error_dict[channel] += error_dict[channel]
                                tol = info['tol']
                                self.p2v_fidelity_test(error_dict[channel], tol, channel)

                # Print the total error for each channel
                for channel, error in error_dict.items():
                    print(f"Current error for {channel}: {error}")

                time.sleep(self.twin_rate)

        for channel, total_error in total_error_dict.items():
            print(f"Total error for {channel}: {total_error}")
            print(f"mirroring coefficient for {channel}: {self.mirrcoeff[channel]}")
            print(f"mirroring coefficient in time for {channel}: {self.mirrcoeff_t[channel]}")

        self.write_mirrcoeff_t()  # Call the function to write to the file
    def p2v_fidelity_test(self, error, tol, channel):
        if error < tol:
            self.mirrcount[channel] += 1
            print('mirroring achieved')

        self.mirrcoeff[channel] = self.mirrcount[channel] / (self.TMax / self.twin_rate + 1) * 1e2
        self.mirrcoeff_t[channel].append(self.mirrcoeff[channel])

    def write_mirrcoeff_t(self, filename="mirrcoeff_t.csv"):
        # Check if the directory exists and create it if necessary
        outdir = "output"
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # Creating DataFrame from mirrcoeff_t dictionary
        df = pd.DataFrame(self.mirrcoeff_t)

        # Writing DataFrame to CSV
        df.to_csv(os.path.join(outdir, filename), index=False)


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
