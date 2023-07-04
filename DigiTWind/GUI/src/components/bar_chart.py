from dash import Dash, dcc, html
import plotly.express as px
from . import ids
from dash.dependencies import Input, Output
MEDAL_DATA = px.data.medals_long()
def render(app: Dash) -> html.Div:
    @app.callback(
        Output(ids.BAR_CHART, "children"),
        Input(ids.NATION_DROPDOWN,"value")
    )
    def update_bar_chart(nations: list[str]) -> html.Div:
        filtered_data = MEDAL_DATA.query("nation in @nations")
        if filtered_data.shape[0] == 0:
            return html.Div("No Data selected.")
        fig = px.bar(filtered_data, x="medal", y="count", color="nation", text="nation")
        return html.Div(dcc.Graph(figure=fig), id=ids.BAR_CHART)

    return html.Div(id=ids.BAR_CHART)