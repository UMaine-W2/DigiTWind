from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from . import ids
import pandas as pd
import numpy as np
#
# class Displacement:
#     def __init__(self):
#         self.surge = 0
#         self.sway  = 0
#         self.heave = 0
#         self.roll  = 0
#         self.pitch = 0
#         self.yaw   = 0
#
#     def update_disp(self, vdata):
#
#         if len(vdata.keys()) == 0:
#             self.surge = 0
#             self.sway  = 0
#             self.heave = 0
#             self.roll  = 0
#             self.pitch = 0
#             self.yaw   = 0
#         else:
#             last_second = max(vdata.keys())
#             self.surge = vdata[last_second]['Surge']
#             self.sway  = vdata[last_second]['Sway']
#             self.heave = vdata[last_second]['Heave']
#             self.roll  = np.deg2rad(vdata[last_second]['Roll'])
#             self.pitch = np.deg2rad(vdata[last_second]['Pitch'])
#             self.yaw   = np.deg2rad(vdata[last_second]['Yaw'])

# def rotation_matrix(roll, pitch, yaw):
#     R_x = np.array([[1, 0, 0],
#                     [0, np.cos(roll), -np.sin(roll)],
#                     [0, np.sin(roll), np.cos(roll)]])
#
#     R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
#                     [0, 1, 0],
#                     [-np.sin(pitch), 0, np.cos(pitch)]])
#
#     R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
#                     [np.sin(yaw), np.cos(yaw), 0],
#                     [0, 0, 1]])
#
#     R = np.dot(R_z, np.dot(R_y, R_x))
#     return R


# def animator(data, disp):
#     animated = data.copy()
#     animated.reset_index(drop=True, inplace=True)
#     animated["x"] = animated["x_original"] + disp.surge
#     animated["y"] = animated["y_original"] + disp.sway
#     animated["z"] = animated["z_original"] + disp.heave
#
#     # Get the rotation matrix for the given roll, pitch, and yaw
#     R = rotation_matrix(disp.roll, disp.pitch, disp.yaw)
#
#     # Apply the rotation matrix to each point
#     for i in range(len(animated)):
#         point = np.array([animated.loc[i, "x"], animated.loc[i, "y"], animated.loc[i, "z"]])
#         rotated_point = np.dot(R, point)
#         animated.loc[i, ["x", "y", "z"]] = rotated_point
#
#     return animated



def create_3d_figure(mesh_data, vdata):
    min_val = mesh_data[['x', 'y', 'z']].min().min()
    max_val = mesh_data[['x', 'y', 'z']].max().max()

    # disp = Displacement()
    # disp.update_disp(vdata)
    # animated_data = animator(mesh_data, disp)

    traces = [
        go.Scatter3d(
            x=mesh_data["x"], #x=animated_data["x"] if you want it animated
            y=mesh_data["y"], #y=animated_data["y"] if you want it animated
            z=mesh_data["z"], #z=animated_data["z"] if you want it animated
            mode='markers',
            marker=dict(size=2)
        )
    ]

    layout = go.Layout(
        scene=dict(
            xaxis=dict(range=[min_val, max_val]),
            yaxis=dict(range=[min_val, max_val]),
            zaxis=dict(range=[min_val, max_val]),
            aspectmode='cube',
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=1.5, y=-1.5, z=0.5),
            ),
        ),
        autosize=False,
        width=900,  # Set the width and height to your desired values
        height=900,
    )

    return go.Figure(data=traces, layout=layout)


def render(retina, mesh_data, vdata):
    graph = dcc.Graph(
        id={'type': 'dynamic-graph'},
        figure=create_3d_figure(mesh_data, vdata)
    )

    graph_container = html.Div(children=graph, id='3d-graph-container')

    # update_graph_callback(retina)

    return html.Div(
        children=[graph_container],
    )

#
# def update_graph_callback(retina):
#     @retina.callback(
#         Output({'type': 'dynamic-graph'}, 'figure'),
#         Input(ids.INTERVAL_COMPONENT, 'n_intervals')
#     )
#     def update_graph(n_intervals):
#         if len(retina.vdata.keys()) != 0:
#             # Get the latest second's data
#             last_second = max(retina.vdata.keys())
#             last_second_data = retina.vdata[last_second]
#
#             dof_keys = ['Surge', 'Sway', 'Heave', 'Roll', 'Pitch', 'Yaw']
#
#             # Check if all degrees of freedom are available in the latest second's data
#             if all(key in last_second_data for key in dof_keys):
#                 return create_3d_figure(retina.mesh_data, retina.vdata)  # make sure retina.mesh_data is passed here
#             else:
#                 return go.Figure()  # return an empty figure
#
#
