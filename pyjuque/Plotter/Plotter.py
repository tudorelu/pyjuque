import plotly.graph_objs as go
from plotly.offline import plot
from pandas import DataFrame
from numpy import array
from .Utils import GraphDetails, round_decimals_down
from .Exceptions import GraphDetailsError, SourceNotFoundError
from uuid import uuid4

def create_plot(df:DataFrame, 
                all_graphs_details:list,
                show_price:bool=True,
                show_candles:bool=False,
                show_volume:bool=False,
                price_kwargs:dict=None,
                figure_kwargs:dict=None,
                layout_kwargs:dict=None,
                title:str = None,
                use_figure_widget:bool = False,
                y_axes_split:str = 'equal',             # 'equal' or 'one_dominant'
                ) -> go.FigureWidget:
    """
    #### Returns a plotly figure object with the data from the provided all_graphs_details.
    """
    if figure_kwargs is None:
        figure_kwargs = {}
    if layout_kwargs is None:
        layout_kwargs = {}
    if price_kwargs is None:
        price_kwargs = {}
    # Compute plotting data
    data = []
    y_axes = []
    if show_candles:
        data.append(_get_candle_graph_object(df, **price_kwargs))
    else:
        if show_price:
            data.append(_get_scatter_graph_object(df, name='Price', **price_kwargs))
    if show_volume:
        data.append(_get_bar_graph_object(df, y='volume', yaxis='y2'))
        y_axes.append('y2')
    for gd in all_graphs_details:
        data.append(_graph_details_to_graph_object(df, gd))
        y_axes.append(gd.yaxis)
    y_axes = set(y_axes)
    # Create layout and update y axes
    layout = _get_boilerplate_layout(title=title, **layout_kwargs)
    if y_axes_split == 'equal':
        domains = _get_y_axes_domains_equal_splits(len(y_axes))
    elif y_axes_split == 'one_dominant':
        domains = _get_y_axes_domains_one_dominant(len(y_axes))
    else:
        raise ValueError('y_axes_split must be "equal" or "one_dominant"')
    layout = _update_layout_y_axes(layout, domains)
    if use_figure_widget:
        fig = go.FigureWidget(data = data, layout = layout, **figure_kwargs)
    else:
        fig = go.Figure(data = data, layout = layout, **figure_kwargs)
    fig.update_layout(autosize=True)
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


def show_plot(fig:go.FigureWidget):
    plot(fig, auto_open=True)


def save_plot(fig:go.FigureWidget, title:str=None):
    if title is None:
        title = f"Plot_{str(uuid4()).split('-')[3]}"
    plot(fig, filename=f'{title}.html', auto_open=False)


def _get_boilerplate_layout(**kwargs):
    return go.Layout(
        margin={'l':0, 'r':0, 'b':0, 't':30},
        hovermode="closest", plot_bgcolor="#FFF", paper_bgcolor="#FFF",
        legend={'font':{'size':8}, 'orientation':'h', 'x':0, 'y':0},
        xaxis={'rangeslider': { 'visible': False,
                                'yaxis': {'rangemode':'match'}}, 
                'showticklabels':False, 'type': 'date'},
        **kwargs)


def _update_layout_y_axes(layout, domains:list=None):
    if domains is None:
        domains = [(0, 1)]
    layout.update(
        yaxis={'domain': domains[0], 'fixedrange': False,
            'showticklabels': False, 'ticks': ''})
    yaxis_num = 1
    for dom in domains[1:]:
        axis_name = f'yaxis{yaxis_num+1}'
        layout.update(**{axis_name:{'domain': dom, 'showticklabels': False}})
        yaxis_num+=1
    return layout


def _get_y_axes_domains_equal_splits(y_axes:int=2):
    if y_axes < 0:
        raise ValueError('y_axes must be at least 0')
    if y_axes <= 1:
        return [(0, 1)]
    split_width = 100 / y_axes 
    prev_split = 100 - split_width
    domains = [(round(prev_split / 100, 2), 1)]
    for _ in range(y_axes-1):
        current_split = prev_split - split_width
        domains.append((
                round(current_split / 100, 2), 
                round(prev_split / 100, 2)
            ))
        prev_split = current_split
    return domains


def _get_y_axes_domains_one_dominant(y_axes:int=2):
    if y_axes < 0:
        raise ValueError('y_axes must be at least 0')
    if y_axes <= 1:
        return [(0, 1)]
    split_width = round_decimals_down(0.5 / (y_axes-1)) 
    domains = [(0.5, 1)]
    prev_split = 0.5
    for _ in range(y_axes-1):
        current_split = round(prev_split - split_width, 2)
        domains.append((current_split, prev_split))
        prev_split = current_split
    return domains


def _graph_details_to_graph_object(df:DataFrame, 
                            graph_details:GraphDetails) -> go.FigureWidget:
    xs, ys = _extract_xy_values_from_graph_details(df, graph_details)
    if graph_details.type == 'bar':
        return go.Bar(      
                x = xs, y = ys,
                name = graph_details.name,
                xaxis = graph_details.xaxis,
                yaxis = graph_details.yaxis,
                width = graph_details.width,
                showlegend = graph_details.showlegend,
                **graph_details.extra_kwargs)
    marker_kwargs = {}
    if graph_details.mode == 'markers':
        marker_kwargs = dict(
            marker_size = graph_details.marker_size,
            marker_color = graph_details.color,
            marker_symbol = graph_details.marker_symbol)
    return go.Scatter(
                x = xs, y = ys, 
                name = graph_details.name,
                xaxis = graph_details.xaxis,
                yaxis = graph_details.yaxis,
                mode = graph_details.mode,
                showlegend = graph_details.showlegend,
                **marker_kwargs,
                **graph_details.extra_kwargs)


def _get_candle_graph_object(df:DataFrame, x:str='time', open_src:str='open', 
                        high_src:str='high', low_src:str='low', close_src:str='close', 
                                            **kwargs) -> go.FigureWidget:
    return go.Candlestick(
                name = 'Candles', x = df[x],
                open = df[open_src], close = df[close_src],
                high = df[high_src], low = df[low_src], **kwargs)


def _extract_data_points_from_source(
                source:str or list or array, df:DataFrame) -> list or array:
    if type(source) == str:
        if source in df.columns:
            return df[source]
        else:
            raise SourceNotFoundError(
                f'No column found in df for {source}')
    return source


def _get_scatter_graph_object(df:DataFrame, x:str='time', 
                y:str or list or array='close', **kwargs) -> go.FigureWidget:
    x = _extract_data_points_from_source(x, df)
    y = _extract_data_points_from_source(y, df)
    return go.Scatter(x = x, y = y, **kwargs)


def _get_bar_graph_object(df:DataFrame, x:str='time', 
                y:str or list or array='close', **kwargs) -> go.FigureWidget:
    x = _extract_data_points_from_source(x, df)
    y = _extract_data_points_from_source(y, df)
    return go.Bar(x = x, y = y, **kwargs)


def _extract_xy_values_from_graph_details(df:DataFrame, 
                graph_details:GraphDetails) -> tuple:
    """ Best effort to extract x and y values from graph_details."""
    y_vals = None
    if graph_details.ysource is None:
        if graph_details.name in df.columns:
            y_vals = df[graph_details.name]
        else:
            raise SourceNotFoundError(
                f'No ysource found for the graph of {graph_details.name}')
    elif type(graph_details.ysource) != str:
        y_vals = graph_details.ysource
    else:
        if graph_details.ysource in df.columns:
            y_vals = df[graph_details.ysource]
        elif graph_details.name in df.columns:
            y_vals = df[graph_details.name]
        else:
            raise SourceNotFoundError(
                f'No ysource found for the graph of {graph_details.name}')
    x_vals = None
    if graph_details.xsource is None:
        raise SourceNotFoundError(
            f'No xsource found for the graph of {graph_details.name}')
    if type(graph_details.xsource) != str:
        x_vals = graph_details.xsource
    else:
        if graph_details.xsource in df.columns:
            x_vals = df[graph_details.xsource]
        else:
            raise SourceNotFoundError(
                f'No xsource found for the graph of {graph_details.name}')
    if len(x_vals) != len(y_vals):
        raise GraphDetailsError(
            f'Length of x_vals ({len(x_vals)}) and y_vals ({len(y_vals)}) '
            f'are not equal for {graph_details.name}')
    return x_vals, y_vals
