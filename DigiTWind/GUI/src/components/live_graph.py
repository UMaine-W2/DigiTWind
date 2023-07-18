from dash import Dash, dcc, html
from dash.dependencies import Input, Output, ALL
from . import ids
import plotly.graph_objs as go
from plotly.graph_objs import Figure

def render(retina):
    @retina.callback(
        Output(ids.LIVE_GRAPHS, 'children'),
        [Input(ids.STATE_DROPDOWN, 'value'),
         Input(ids.INTERVAL_COMPONENT, 'n_intervals'),
         Input(ids.WINDOW_SIZE, 'value')]
    )
    def update_graphs(selected_states, n, window_size):
        graphs = []
        for state in retina.channels:
            if state in selected_states:
                ptime_values = list(retina.pdata.keys())
                vtime_values = list(retina.vdata.keys())

                # determine the threshold for the last window_size seconds
                ptime_threshold = max(ptime_values) - window_size
                vtime_threshold = max(vtime_values) - window_size

                # filter keys that fall within the last 10 seconds
                pkeys_to_keep = [key for key in ptime_values if key >= ptime_threshold]
                vkeys_to_keep = [key for key in vtime_values if key >= vtime_threshold]

                pdata_values = [retina.pdata[key][state] for key in pkeys_to_keep]
                vdata_values = [retina.vdata[key][state] for key in vkeys_to_keep]

                # use the filtered keys for the x-values
                ptime_values = pkeys_to_keep
                vtime_values = vkeys_to_keep

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
                stats = "Test Name: {}  \n" \
                        "Current error: {:.2f}  \n" \
                        "Error tolerance: {:.2f}%  \n" \
                        "Mirroring coefficient: {:.2f}%  ".format(retina.test_name,
                                                                  retina.current_error_dict[state],
                                                                  retina.channel_info[state]['tol'] * 100,
                                                                  retina.mirrcoeff[state])
                stats_paragraph = dcc.Markdown(stats)

                stats_container = html.Div(children=stats_paragraph, style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'middle'})

                graph_container = html.Div(children=graph, style={'width': '70%', 'display': 'inline-block', 'vertical-align': 'middle'})

                # Add a subheading before each graph
                subheading = html.H3(f"Data for {state}")

                graph_and_stats = html.Div(children=[subheading, graph_container, stats_container])
                graphs.append(graph_and_stats)

        return graphs

    return html.Div(id=ids.LIVE_GRAPHS)
