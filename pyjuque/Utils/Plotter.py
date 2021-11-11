import os
import plotly.graph_objs as go
from plotly.offline import plot
import random
from pandas.core.series import Series
from pandas.core.frame import DataFrame
from pandas import to_datetime, Timestamp
from datetime import datetime
import pytz
"""
    This file contains all the tools used for plotting data.

    It currently contains a general purpose plotting function which plots 
    candlestick charts, overlayed with indicators, signals, & trendlines.

    Eventually, there should be more functions here, each of which would solve a 
    single purpose, to provide more flexibility to developers as to what to plot 
    and how to style it. Modular is the aim.
"""

# TI & TA
def GetPlotData(df, 
    add_volume:bool=True,
    add_candles:bool=True,
    ignore_price:bool=False,
    buy_signals:bool or list=False,
    sell_signals:bool or list=False,
    signals:bool or list=False,
    regimes_number=None,
    plot_indicators=[],
    trend_points=False,
    use_scattergl=False,
    convert_to_date=False,
    trends=False):
    """ Generates the plotly traces to be plotted. """
    scatter_type = go.Scatter
    if use_scattergl:
        scatter_type = go.Scattergl
    data = []
    time_format = "%Y-%m-%d %H:%M"
    utc_date = df['time']
    def ts_to_s(x):
        return datetime.fromtimestamp(x, tz=pytz.UTC).strftime(time_format)
    if convert_to_date:
        if 'date' in df.columns:
            utc_date = df['date']
        else:
            utc_date = list(map(ts_to_s, df.time))
    if add_candles and not ignore_price:
        candle = go.Candlestick(
            x = utc_date,
            open = df['open'],
            close = df['close'],
            high = df['high'],
            low = df['low'],
            increasing_line_color = 'lightseagreen', 
            decreasing_line_color = 'lightcoral',
            name = "Candlesticks")
        data.append(candle)
    elif not ignore_price:
        price = scatter_type( 
            x = utc_date,
            y = list(df['close'].values), 
            name = 'Price',
            line = dict(color = 'black'))
        data.append(price)
    else:
        pass
    if add_volume:
        volume = go.Bar(
            x = utc_date,	
            y = df['volume'], 
            xaxis="x", 
            yaxis="y2", 
            # width = 400000,
            name = "Volume")
        data.append(volume)
    for ind in plot_indicators:
        custom_source = ind.get('source', False)
        if custom_source or df.__contains__(ind['name']):
            if ind.get('showlegend', None) is None:
                ind['showlegend'] = True
            if ind.get('xvalue', None) is None:
                ind['xvalue'] = 'time'
            if ind.get('color', None) is None:
                ind['color'] = None # 'rgba(102, 207, 255, 50)'
            if ind.get('yaxis', None) is None:
                ind['yaxis'] = 'y'
            if ind.get('xaxis', None) is None:
                ind['xaxis'] = 'x'
            if ind.get('type', None) is None:
                if use_scattergl:
                    ind['type'] = 'scattergl'
                else:
                    ind['type'] = 'scatter'
            if ind.get('width', None) is None:
                ind['width'] = 300000
            if ind.get('fill', None) is None:
                ind['fill'] = None
            if ind.get('mode', None) is None:
                ind['mode'] = 'lines'
            if ind.get('custom_x', None) is None:
                ind['custom_x'] = False

            x_source = []
            y_source = []
            # print('custom_source')
            # print(ind['title'])
            # print(custom_source)
            if custom_source:
                for entry in custom_source:
                    if not ind['custom_x'] and convert_to_date:
                        dt = datetime.fromtimestamp(entry[0], tz=pytz.UTC)
                        x_source.append(dt.strftime(time_format))
                    else:
                        x_source.append(entry[0])
                    y_source.append(entry[1])
            else:
                if not ind['custom_x'] and convert_to_date:
                    # to_datetime(df[ind['xvalue']] * 1_000_000, utc=True, format=(time_format))
                    # dt = datetime.fromtimestamp(df[ind['xvalue']], tz=pytz.UTC)
                    # x_source.append(dt.strftime(time_format))
                    x_source = list(map(ts_to_s, df[ind['xvalue']]))
                else:
                    x_source = df[ind['xvalue']]
                y_source = df[ind['name']]
            if ind['type'] == 'bar':
                trace = go.Bar(
                    x = x_source, 
                    y = y_source, 
                    name = ind['title'],
                    xaxis = ind['xaxis'], 
                    yaxis = ind['yaxis'], 
                    marker_color = ind['color'], 
                    showlegend = ind['showlegend'],
                    width = ind['width'],
                marker = dict(color = ind['color']))
            else:
                trace = scatter_type( 
                    x = x_source,
                    y = y_source, 
                    name = ind['title'],
                    mode = ind['mode'], 
                    xaxis = ind['xaxis'], 
                    yaxis = ind['yaxis'], 
                    fill = ind['fill'], 
                    showlegend = ind['showlegend'],
                    line = dict(color = ind['color']))

            data.append(trace)
    if trend_points:
        mins = scatter_type( 
            x = utc_date,
            y = df['min'], 
            name = "Min Points",
            line = dict(color = ('rgba(255, 100, 100, 255)')),
            mode = "markers",)
        data.append(mins)
        maxs = scatter_type( 
            x = utc_date, 
            y = df['max'], 
            name = "Max Points",
            line = dict(color = ('rgba(100, 255, 100, 255)')),
            mode = "markers",)
        data.append(maxs)
    if signals:
        for signal in signals:
            size_multiplier = [15 for z in signal["points"]]
            if len(signal["points"]) > 1:
                if len(signal["points"][0]) > 2:
                    size_multiplier = [z[2] for z in signal["points"]]
            marker_symbol = 'circle'
            if signal.get('marker_symbol', None) is not None:
                marker_symbol = signal['marker_symbol']
            marker_color = 'blue'
            if signal.get('marker_color', None) is not None:
                marker_color = signal['marker_color']
            xs = []
            if convert_to_date:
                for entry in signal['points']:
                    dt = datetime.fromtimestamp(entry[0], tz=pytz.UTC)
                    xs.append(dt.strftime(time_format))
            else:
                xs = [item[0] for item in signal['points']]
            scat = scatter_type(
                x = xs,
                y = [item[1] for item in signal['points']],
                name = signal['name'],
                mode = "markers",
                marker_size = size_multiplier,
                marker_symbol = marker_symbol,
                marker_color = marker_color
            )
            data.append(scat)
    return data


def PlotData(df,
    add_candles:bool=False,
    add_volume:bool=False,
    ignore_price:bool=False,
    buy_signals:bool or list=False,
    sell_signals:bool or list=False,
    signals:bool or list=False,
    trend_points=False,
    plot_indicators=[],
    plot_shapes=False,
    regimes_number=None,
    trends=False,
    save_plot=False,
    show_plot=False,
    stats=None,
    tt_split=None,
    use_scattergl=False,
    convert_to_date=False,
    use_figure_widget=False,
    plot_title:str="Unnamed"):
    '''
    Creates a plotly plot based on the options provided - which can be displayed
    in a front-end or saved as a standalone webpage.

    Params
    --
        buy signals: bool or list
            if not False it adds to the plot some points representing buy signals

        sell signals: bool or list
            if list, it adds to the plot some points representing sell signals

    '''
    data = GetPlotData(
        df,
        add_candles=add_candles,
        add_volume=add_volume,
        ignore_price=ignore_price,
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        signals=signals,
        regimes_number=regimes_number,
        trend_points=trend_points,
        plot_indicators=plot_indicators,
        use_scattergl=use_scattergl,
        convert_to_date=convert_to_date,
        trends=trends)
    xaxis_type = 'date'
    if convert_to_date:
        xaxis_type = 'category'
    layout = go.Layout(
        # autosize=True,
        margin=dict(l=0, r=0, b=0, t=0),
        hovermode="closest",
        plot_bgcolor="#FFF",
        paper_bgcolor="#FFF",
        legend=dict(font=dict(size=8), orientation="h", x=0, y=0),
        # colorway=['#5E0DAC', '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
        xaxis={
            'rangeslider': {
                'visible': False,
                'yaxis': {
                    'rangemode':'match'
                }
            }, 
            "showticklabels":False,
            'type': xaxis_type},
    )
    y2, y3, y4 = False, False, False
    if add_volume:
        y2 = True
    for ind in plot_indicators:
        if ind.__contains__('yaxis'):
            if ind['yaxis'] == 'y2':
                y2 = True
            if ind['yaxis'] == 'y3':
                y3 = True
            if ind['yaxis'] == 'y4':
                y4 = True

    if y2 and y3 and y4:
        layout.update(
            yaxis={
                "domain": [0.55, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False,
            })
        layout.update(
            yaxis2=dict(
                domain = [0.36, 0.54],
                side = 'right',
                showticklabels = False,
                # title  = "Volume"
            ))
        layout.update(
            yaxis3=dict(
                domain = [0.17, 0.35],
                showticklabels = False,
                # title=""
            ))
        layout.update(
            yaxis4=dict(
                domain = [0, 0.16],
                showticklabels = False,
                # title=""
            ))
    elif (y2 and y3) or (y2 and y4) or (y3 and y4):
        layout.update(
            yaxis={
                "domain": [0.5, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )
        layout.update(
            yaxis2=dict(
                domain = [0.25, 0.49],
                side = 'right',
                showticklabels = False,
                # title  = "Volume"
                ))
        layout.update(
            yaxis3=dict(
                domain = [0, 0.24],
                showticklabels = False,
                # title=""
            ))
    elif y2:
        layout.update(
            yaxis={
                "domain": [0.4, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )
        layout.update(
            yaxis2=dict(
                domain = [0, 0.39],
                showticklabels = False,
                # ticks="",
                # title=""
                ))
    elif y3:
        layout.update(
            yaxis={
                "domain": [0.4, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )
        layout.update(
            yaxis3=dict(
                domain = [0, 0.39],
                showticklabels = False,
                # ticks="",
                # title=""
                ))
    elif y4:
        layout.update(
            yaxis={
                "domain": [0.4, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )
        layout.update(
            yaxis4=dict(
                domain = [0, 0.39],
                showticklabels = False,
                # ticks="",
                # title=""
                ))
    else:
        layout.update(
            yaxis={
                "domain": [0.05, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )
    if trends:
        layout.update(shapes=layout['shapes'].__add__(tuple(trends)))
    if plot_shapes:
        layout.update(shapes=layout['shapes'].__add__(tuple(plot_shapes)))
    if stats != None:
        data, layout = add_stats(stats, data, layout)
    # style and display
    if use_figure_widget:
        fig = go.FigureWidget(data = data, layout = layout)
    else:
        fig = go.Figure(data = data, layout = layout)

    if tt_split != None:
        fig = add_tt_split(df, fig, tt_split)
    
    if save_plot or show_plot:
        file_path = os.path.abspath('graphs')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        plot(fig, filename=os.path.join(file_path, plot_title+'.html'), auto_open=show_plot)

    return fig

########################################################
###                 HELPER FUNCTIONS
########################################################

def add_tt_split(df, fig, train_test_split=0.5):
    """ Makes one section of the bg of the figure blue 
    (train) and another part red (test) """
    l_df = len(df)
    idx = int(l_df * train_test_split)
    fig.add_vrect(
        x0=df.time.values[0], x1=df.time.values[idx-1],
        fillcolor="PaleTurquoise", opacity=0.5,
        layer="below", line_width=0,
    )
    fig.add_vrect(
        x0=df.time.values[idx], x1=df.time.values[l_df-1],
        fillcolor="LightSalmon", opacity=0.5,
        layer="below", line_width=0,
    )
    return fig


def add_stats(stats, data, layout):
    """ Adds a table with stats about the data to the fig """
    stat_names = []
    stat_vals = []
    for stat in stats.keys():
        if type(stats[stat]) not in [Series, DataFrame]:
            stat_names.append(stat)
            stat_vals.append(round(stats[stat], 4))
    table = go.Table(
        header=dict(
            values=["Performance Indicators", "<b>Values</b>"],
            # line_color='white', fill_color='white',
            align='center', font=dict(color='black', size=12)
        ),
        cells=dict(
            values=[stat_names, stat_vals],
            # line_color=[df.Color], fill_color=[df.Color],
            align='center', font=dict(color='black', size=12)
        ),
        domain=dict(x=[0.76, 1], y=[0, 1]))
    data.append(table)
    layout.update(
        xaxis={
            "domain": [0, 0.75],
            'rangeslider': {
                'visible': False,
                'yaxis': {
                    'rangemode':'match'
                }
            }, 
            "showticklabels":False,
            'type': 'date'})
    return data, layout
