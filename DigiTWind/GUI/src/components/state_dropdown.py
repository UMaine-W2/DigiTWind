from dash import Dash, dcc, html
from dash.dependencies import Input, Output

from . import ids


def render(retina):
    all_states: list[str] = retina.channels

    @retina.callback(
        Output(ids.STATE_DROPDOWN, "value"),
        Input(ids.SELECT_ALL_STATES_BUTTON, "n_clicks"),
    )
    def select_all_states(_: int) -> list[str]:
        return all_states

    return html.Div(
        children=[
            html.H6("State", style={"fontSize": "18px"}),
            dcc.Dropdown(
                id=ids.STATE_DROPDOWN,
                options=[{"label": state, "value": state} for state in all_states],
                value=all_states,
                multi=True,
            ),
            html.Button(
                className="dropdown-button",
                children=["Select All"],
                id=ids.SELECT_ALL_STATES_BUTTON,
                n_clicks=0,
            ),
        ]
    )
