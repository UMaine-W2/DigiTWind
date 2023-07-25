# Copyright 2023 - Yuksel Rudy Alkarem

from dash import Dash, html, dcc
from .src.components import state_dropdown, live_graph, window_size, visual_3d
from .src.components import ids
import pandas as pd
import os
from io import StringIO

class Retina(Dash):
    def __init__(self, brain):
        super().__init__()
        self.title              = brain.title
        self.test_name          = brain.test_name
        self.channels           = brain.channels_L[1:] # without time (user-friendly labels)
        self.pdata              = brain.memory.shared_pdata
        self.vdata              = brain.memory.shared_vdata
        self.twin_rate          = brain.twin_rate
        self.current_error_dict = brain.memory.current_error_dict
        self.channel_info       = brain.channel_info
        self.mirrcoeff          = brain.memory.mirrcoeff
        self.tol                = brain.tol

        self.mesh_file_path     = brain.model_config.mesh_file_path
        self.mesh_data          = self.load_mesh_data(self.mesh_file_path)
        print(self.mesh_data)

        # Define the layout
        self.layout = self.create_layout()

    def create_layout(self):
        return html.Div(
            className="app-div",
            children=[
                html.H1(self.title),
                html.Hr(),
                state_dropdown.render(self),
                window_size.render(),
                live_graph.render(self),  # This will be 'graph-container' Div
                visual_3d.render(self, self.mesh_data, self.vdata),
                dcc.Interval( # New Interval component
                    id=ids.INTERVAL_COMPONENT,
                    interval=self.twin_rate*1000, # in milliseconds
                    n_intervals=0
                )
            ]
        )

    def run_(self, debug=False, host='127.0.0.1'):
        self.run_server(debug=debug, host=host, threaded=True)

    def load_mesh_data(self, file_path):
        print("Loading data from: ", file_path)

        with open(file_path, 'r') as f:
            lines = f.readlines()[:-2]  # read all lines except the last two
            data_str = ''.join(lines)

        # Skip the first 4 rows as they do not contain mesh data
        data = pd.read_csv(StringIO(data_str), skiprows=4, sep="\s+", header=None, usecols=[0, 1, 2])

        # Name the columns for easier access
        data.columns = ["x", "y", "z"]

        # Create a new DataFrame with y values negated
        data_neg_y = data.copy()
        data_neg_y["y"] = -data["y"]

        # Concatenate old data with new DataFrame
        data = pd.concat([data, data_neg_y])

        # Save the original x values
        data['x_original'] = data['x'].copy()
        data['y_original'] = data['y'].copy()
        data['z_original'] = data['z'].copy()
        return data