# Copyright 2023 - Yuksel Rudy Alkarem

from dash import Dash, html, dcc
from .src.components import state_dropdown, live_graph
from .src.components import ids

class Retina(Dash):
    def __init__(self, brain):
        super().__init__()
        self.title              = brain.title
        self.test_name          = brain.test_name
        self.channels           = brain.channels[1:] # without time
        self.pdata              = brain.memory.shared_pdata
        self.vdata              = brain.memory.shared_vdata
        self.twin_rate          = brain.twin_rate
        self.current_error_dict = brain.memory.current_error_dict
        self.channel_info       = brain.channel_info
        self.mirrcoeff          = brain.memory.mirrcoeff

        # Define the layout
        self.layout = self.create_layout()


    def create_layout(self):
        return html.Div(
            className="app-div",
            children=[
                html.H1(self.title),
                html.Hr(),
                state_dropdown.render(self),
                live_graph.render(self),  # This will be 'graph-container' Div
                dcc.Interval( # New Interval component
                    id=ids.INTERVAL_COMPONENT,
                    interval=self.twin_rate*1000, # in milliseconds
                    n_intervals=0
                )
            ]
        )

    def run_(self, debug=False, host='127.0.0.1'):
        self.run_server(debug=debug, host=host)