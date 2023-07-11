from dash import Dash, dcc, html
from dash.dependencies import Input, Output, ALL
from . import ids
import plotly.graph_objs as go
from plotly.graph_objs import Figure

def render(retina):
    @retina.callback(
        Output(ids.LIVE_GRAPHS, 'children'),
        [Input(ids.STATE_DROPDOWN, 'value'),
         Input(ids.INTERVAL_COMPONENT, 'n_intervals')]
    )
    def update_graphs(selected_states, n):
        graphs = []
        for state in retina.channels:
            if state in selected_states:
                pdata_values = [retina.pdata[key][state] for key in retina.pdata.keys()]
                vdata_values = [retina.vdata[key][state] for key in retina.vdata.keys()]
                ptime_values = list(retina.pdata.keys())
                vtime_values = list(retina.vdata.keys())

                traces = [
                    go.Scatter(
                        x=ptime_values,
                        y=pdata_values,
                        mode='lines',
                        name=f'{state} pdata'
                    ),
                    go.Scatter(
                        x=vtime_values,
                        y=vdata_values,
                        mode='lines',
                        name=f'{state} vdata'
                    )
                ]

                layout = go.Layout(
                    xaxis=dict(
                        title="t [s]",
                        titlefont=dict(
                            family="Courier New, monospace",
                            size=18,
                            color="#7f7f7f"
                        )
                    ),
                    yaxis=dict(
                        title=state,
                        titlefont=dict(
                            family="Courier New, monospace",
                            size=18,
                            color="#7f7f7f"
                        )
                    )
                )
                graph = dcc.Graph(
                    id={'type': 'dynamic-graph', 'index': state},
                    figure=go.Figure(data=traces, layout=layout)
                )

                # Mirroring Reporting
                stats = "Current error: {:.2f}  \n" \
                        "error tolerance: {:.2f}% \n" \
                        "Mirroring Coefficient: {:.2f}%".format(retina.current_error_dict[state], retina.channel_info[state]['tol'] * 100, retina.mirrcoeff[state])
                stats_paragraph = dcc.Markdown(stats)
                stats_container = html.Div(children=stats_paragraph, style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'middle'})

                graph_container = html.Div(children=graph, style={'width': '70%', 'display': 'inline-block', 'vertical-align': 'middle'})

                # Add a subheading before each graph
                subheading = html.H3(f"Data for {state}")

                graph_and_stats = html.Div(children=[subheading, graph_container, stats_container])
                graphs.append(graph_and_stats)

        return graphs

    return html.Div(id=ids.LIVE_GRAPHS)
