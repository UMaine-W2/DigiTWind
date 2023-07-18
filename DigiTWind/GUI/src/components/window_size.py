from dash import Dash, dcc, html

from . import ids

def render():
    return html.Div(
        children=[
            html.Label("Enter window size in seconds:"),
            dcc.Input(id=ids.WINDOW_SIZE, type="number", value=10), # default to 10 seconds
        ]
    )
