from pytest import raises

# Functions
from pyjuque.Plotter import (
    create_plot,
    GraphDetails)

# Internal Functions
from pyjuque.Plotter.Plotter import (
    _extract_xy_values_from_graph_details, 
    _get_y_axes_domains_equal_splits,
    _get_y_axes_domains_one_dominant,
)

# Exceptions
from pyjuque.Plotter import (GraphDetailsError, SourceNotFoundError)
from .utils import df, long_signals_df, short_signals_df

######### Tests final result

def test_create_plot(df, long_signals_df, short_signals_df):
    longs_graph = GraphDetails(
        name='Long Signals', mode='markers', 
        xsource=long_signals_df.time.values, 
        ysource=long_signals_df.close.values)
    shorts_graph = GraphDetails(
        name='Short Signals', mode='markers', 
        xsource=short_signals_df.time.values,
         ysource=short_signals_df.close.values)
    third_yaxis_graph = GraphDetails(
        name='low', color='red', yaxis='y3')
    fourth_yaxis_graph = GraphDetails(
        name='low', color='red', yaxis='y4')
    graphs = [longs_graph, shorts_graph]

    fig = create_plot(df, all_graphs_details=graphs)
    fig.layout.yaxis
    with raises(AttributeError):
        fig.layout.yaxis2

    fig = create_plot(df, all_graphs_details=graphs, show_volume=True)
    # We should not have an error here
    fig.layout.yaxis
    fig.layout.yaxis2
    with raises(AttributeError):
        fig.layout.yaxis3

    fig = create_plot(df, 
        all_graphs_details=[longs_graph, shorts_graph, third_yaxis_graph])
    # We should not have an error here
    fig.layout.yaxis
    fig.layout.yaxis2
    with raises(AttributeError):
        fig.layout.yaxis3

    fig = create_plot(df, show_volume=True, 
        all_graphs_details=[longs_graph, shorts_graph, third_yaxis_graph])
    fig.layout.yaxis
    fig.layout.yaxis2
    fig.layout.yaxis3
    with raises(AttributeError):
        fig.layout.yaxis4

    fig = create_plot(df, show_volume=True, 
        all_graphs_details=[
            longs_graph, shorts_graph, third_yaxis_graph, fourth_yaxis_graph])
    # We should not have any error here
    fig.layout.yaxis
    fig.layout.yaxis2
    fig.layout.yaxis3
    fig.layout.yaxis4


######### Tests for extracting the layout of the y axes from graph details

def test_get_y_axes_domains_equal_splits():
    assert _get_y_axes_domains_equal_splits(0) == [(0, 1)], \
        'get_y_axes_domains_equal_splits(0) != [(0, 1)]'
    assert _get_y_axes_domains_equal_splits(1) == [(0, 1)], \
        'get_y_axes_domains_equal_splits(1) != [(0, 1)]'

    expected = [(0.5, 1), (0, 0.5)]
    got = _get_y_axes_domains_equal_splits(2)
    print("expected: ", expected)
    print("got: ", got)
    assert got == expected, \
        f'_get_y_axes_domains_equal_splits(2) != {expected}'

    expected = [(0.67, 1), (0.33, 0.67), (0.0, 0.33)]
    got = _get_y_axes_domains_equal_splits(3)
    print("expected: ", expected)
    print("got: ", got)
    assert got == expected, \
        f'_get_y_axes_domains_equal_splits(3) != {expected}'

    expected = [(0.75, 1), (0.50, 0.75), (0.25, 0.5), (0, 0.25)]
    got = _get_y_axes_domains_equal_splits(4)
    print("expected: ", expected)
    print("got: ", got)
    assert got == expected, \
        f'_get_y_axes_domains_equal_splits(4) != {expected}'

    expected = [(0.8, 1), (0.60, 0.8), (0.4, 0.6), (0.2, 0.4), (0, 0.2)]
    got = _get_y_axes_domains_equal_splits(5)
    print("expected: ", expected)
    print("got: ", got)
    assert got == expected, \
        f'_get_y_axes_domains_equal_splits(5) != {expected}'



def test_get_y_axes_domains_one_dominant():
    assert _get_y_axes_domains_one_dominant(0) == [(0, 1)], \
        '_get_y_axes_domains_one_dominant(0) != [(0, 1)]'

    assert _get_y_axes_domains_one_dominant(1) == [(0, 1)], \
        '_get_y_axes_domains_one_dominant(1) != [(0, 1)]'

    expected = [(0.5, 1), (0, 0.5)]
    got = _get_y_axes_domains_one_dominant(2)
    assert got == expected, \
        f'_get_y_axes_domains_one_dominant(2) != {expected}'

    expected = [(0.5, 1), (0.25, 0.5), (0, 0.25)]
    got = _get_y_axes_domains_one_dominant(3)
    assert got == expected, \
        f'_get_y_axes_domains_one_dominant(3) != {expected}'

    expected = [(0.5, 1), (0.34, 0.5), (0.18, 0.34), (0.02, 0.18)]
    got = _get_y_axes_domains_one_dominant(4)
    assert got == expected, \
        f'_get_y_axes_domains_one_dominant(4) != {expected}'



######### Tests for extracting values from graph details

def test_extract_xy_values_from_graph_details_bad_plot(df):
    bad_graph_to_plot = GraphDetails(name='sma')
    with raises(SourceNotFoundError):
        _extract_xy_values_from_graph_details(df, bad_graph_to_plot)


def test_extract_xy_values_from_graph_details_good_plot(df):
    good_graph_to_plot = GraphDetails(name='close')
    x_, y_ = _extract_xy_values_from_graph_details(df, good_graph_to_plot)
    assert x_.equals(df['time']), 'x_ is not equal to df[\'time\']'
    assert y_.equals(df['close']), 'y_ is not equal to df[\'close\']'


def test_extract_xy_values_from_graph_details_custom_source(df):
    bad_graph_to_plot = GraphDetails(name='close', ysource=[1, 2, 3])
    with raises(GraphDetailsError):
        _extract_xy_values_from_graph_details(df, bad_graph_to_plot)
    good_graph_to_plot = GraphDetails(name='close', ysource=df.close)
    x_, y_ = _extract_xy_values_from_graph_details(df, good_graph_to_plot)
    assert x_.equals(df.time), 'x_ is not equal to df[\'time\']'
    assert y_.equals(df.close), 'y_ is not equal to df[\'close\']'


def test_extract_xy_values_from_graph_details_custom_xy_source(df):
    good_graph_to_plot = GraphDetails(name='close', xsource=[1, 2, 3], ysource=[1, 2, 3])
    x_, y_ = _extract_xy_values_from_graph_details(df, good_graph_to_plot)
    assert x_ == [1, 2, 3], 'x_ is not equal to [1, 2, 3]'
    assert y_ == [1, 2, 3], 'y_ is not equal to [1, 2, 3]'


def test_extract_xy_values_from_graph_details_custom_xy_source_2(df):
    good_graph_to_plot = GraphDetails(name='close', xsource=df.close, ysource=df.close)
    x_, y_ = _extract_xy_values_from_graph_details(df, good_graph_to_plot)
    assert x_.equals(df.close), 'x_ is not equal to df[\'close\']'
    assert y_.equals(df.close), 'y_ is not equal to df[\'close\']'

