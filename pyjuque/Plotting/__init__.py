import os
import plotly.graph_objs as go
from plotly.offline import plot
import random

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
    buy_signals:bool or list=False,
    sell_signals:bool or list=False,
    signals:bool or list=False,
    regimes_number=None,
    plot_indicators=[],
    trend_points=False,
    trends=False):
    """ Generates the plotly traces to be plotted. """

    data=[]

    if regimes_number != None:
        if df.__contains__('regime'):
            r_colors = []
            for i in range(regimes_number):
                r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
                rand_str = 'rgba({}, {}, {}, 110)'.format(r, g, b)
                r_colors.append(rand_str)
                print('Color string for regime {} is {}'.format(i, rand_str))

            last_regime = None
            for i, row in df.iterrows():
                if last_regime == None:
                    last_regime = row['regime']
                    regime_start = row
                    continue

                current_regime = row['regime']
                if current_regime == last_regime:
                    continue
                else:
                    regime_end = row
                    data.append(
                        go.Scatter(
                            x=[regime_start['time'],regime_end['time']],
                            y=[30000, 30000],
                            line = dict(
                                color = (r_colors[regime_start['regime']])
                            ),
                            showlegend=False,
                            name = 'Regime {}'.format(regime_start['regime']),
                            fill='tozeroy'))

                    regime_start = regime_end


    if add_volume:
        volume = go.Bar(
            x = df['time'],	
            y = df['volume'], 
            xaxis="x", 
            yaxis="y2", 
            width = 400000,
            name = "Volume")

        data.append(volume)

    if add_candles:
        candle = go.Candlestick(
            x = df['time'],
            open = df['open'],
            close = df['close'],
            high = df['high'],
            low = df['low'],
            name = "Candlesticks")
        data.append(candle)
    else:
        price = go.Scatter( 
            x = df['time'],
            y = df['close'], 
            name = 'Price',
            line = dict(color = 'black'))

        data.append(price)
    
    for ind in plot_indicators:
        if df.__contains__(ind['name']):
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
                ind['type'] = 'scatter'
            if ind.get('width', None) is None:
                ind['width'] = 300000
            if ind.get('fill', None) is None:
                ind['fill'] = None
            if ind.get('mode', None) is None:
                ind['mode'] = 'lines'

            if ind['type'] == 'bar':
                trace = go.Bar(
                    x = df[ind['xvalue']], 
                    y = df[ind['name']], 
                    name = ind['title'],
                    xaxis = ind['xaxis'], 
                    yaxis = ind['yaxis'], 
                    marker_color = ind['color'], 
                    showlegend = ind['showlegend'],
                    width = ind['width'],
                marker = dict(color = ind['color']))
            else:
                trace = go.Scatter( 
                    x = df[ind['xvalue']],
                    y = df[ind['name']], 
                    name = ind['title'],
                    mode = ind['mode'], 
                    xaxis = ind['xaxis'], 
                    yaxis = ind['yaxis'], 
                    fill = ind['fill'], 
                    showlegend = ind['showlegend'],
                    line = dict(color = ind['color']))

            data.append(trace)

    if trend_points:
        mins = go.Scatter( x = df['time'], 	y = df['min'], name = "Min Points",
            line = dict(color = ('rgba(255, 100, 100, 255)')),
            mode = "markers",)
        data.append(mins)

        maxs = go.Scatter( x = df['time'], y = df['max'], name = "Max Points",
                line = dict(color = ('rgba(100, 255, 100, 255)')),
                mode = "markers",)
        data.append(maxs)

    if signals:
        for signal in signals:
            size_multiplier = [10 for z in signal["points"]]
            if len(signal["points"]) > 1:
                if len(signal["points"][0]) > 2:
                    size_multiplier = [z[2] for z in signal["points"]]

            scat = go.Scatter(
                x = [item[0] for item in signal['points']],
                y = [item[1] for item in signal['points']],
                name = signal['name'],
                mode = "markers",
                marker_size = size_multiplier 
            )
            data.append(scat)
    
    return data

def PlotData(df,
    add_candles:bool=True,
    add_volume:bool=True,
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
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        signals=signals,
        regimes_number=regimes_number,
        trend_points=trend_points,
        plot_indicators=plot_indicators,
        trends=trends)

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
            'type': 'date'},
    )
    
    y2, y3 = False, False
    if add_volume:
        y2 = True
    for ind in plot_indicators:
        if ind.__contains__('yaxis'):
            if ind['yaxis'] == 'y2':
                y2 = True
            if ind['yaxis'] == 'y3':
                y3 = True

    if y2 and y3:
        layout.update(
            yaxis={
                "domain": [0.3, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False,
            })
        layout.update(
            yaxis2=dict(
                domain = [0.15, 0.29],
                side = 'right',
                showticklabels = False,
                # title  = "Volume"
            ))
        layout.update(
            yaxis3=dict(
                domain = [0, 0.15],
                showticklabels = False,
                # title=""
            ))
    elif y2:
        layout.update(
            yaxis={
                "domain": [0.25, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )
        layout.update(
            yaxis2=dict(
                domain = [0, 0.24],
                side = 'right',
                showticklabels = False,
                # title  = "Volume"
                ))
    elif y3:
        layout.update(
            yaxis={
                "domain": [0.25, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )
        layout.update(
            yaxis3=dict(
                domain = [0, 0.24],
                showticklabels = False,
                # ticks="",
                # title=""
                ))
    else:
        layout.update(
            yaxis={
                "domain": [0.1, 1],
                # "title": "Price", 
                "fixedrange":False,
                "ticks": '',
                "showticklabels":False},
        )

    if trends:
        layout.update(shapes=layout['shapes'].__add__(tuple(trends)))
    if plot_shapes:
        layout.update(shapes=layout['shapes'].__add__(tuple(plot_shapes)))

    # style and display
    if use_figure_widget:
        fig = go.FigureWidget(data = data, layout = layout)
    else:
        fig = go.Figure(data = data, layout = layout)
    
    if save_plot or show_plot:
        file_path = os.path.abspath('graphs')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        plot(fig, filename=os.path.join(file_path, plot_title+'.html'), auto_open=show_plot)

    return fig
