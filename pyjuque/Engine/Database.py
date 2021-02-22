from pyjuque.Engine.Models import TABotModel as Bot, PairModel as Pair, \
    EntrySettingsModel as EntrySettings, ExitSettingsModel as ExitSettings, getSession

def InitializeDatabaseTaBot(session, params={}):
    """ Function that initializes the database
    by creating a bot with two pairs. """
    name = 'My Bot'
    symbols = []
    quote_asset = None
    starting_balance = 0.001
    test_run = False
    initial_entry_allocation = 25
    signal_distance = 0.3
    profit_target = 2
    stop_loss_value = 0
    exit_on_signal = False

    if params.__contains__('name'):
        assert type(params['name']) == str
        name = params['name']

    if params.__contains__('symbols'):
        assert type(params['symbols']) == list
        symbols = params['symbols']

    if params.__contains__('quote_asset'):
        assert type(params['quote_asset']) == str
        quote_asset = params['quote_asset']

    if params.__contains__('starting_balance'):
        assert type(params['starting_balance']) in [int, float]
        starting_balance = params['starting_balance']

    if params.__contains__('test_run'):
        assert type(params['test_run']) == bool
        test_run = params['test_run']

    if params.__contains__('entry_settings'):
        assert type(params['entry_settings']) == dict
        entry_settings = params['entry_settings']
        if entry_settings.__contains__('initial_entry_allocation'):
            assert type(entry_settings['initial_entry_allocation']) in [int, float]
            initial_entry_allocation = entry_settings['initial_entry_allocation']

        if entry_settings.__contains__('signal_distance'):
            assert type(entry_settings['signal_distance']) in [int, float]
            signal_distance = entry_settings['signal_distance']

    if params.__contains__('exit_settings'):
        assert type(params['exit_settings']) == dict
        exit_settings = params['exit_settings']
        if exit_settings.__contains__('take_profit'):
            assert type(exit_settings['take_profit']) in [int, float]
            profit_target = exit_settings['take_profit']

        if exit_settings.__contains__('stop_loss_value'):
            assert type(exit_settings['stop_loss_value']) in [int, float]
            stop_loss_value = exit_settings['stop_loss_value']

        if exit_settings.__contains__('exit_on_signal'):
            assert type(exit_settings['exit_on_signal']) == bool
            exit_on_signal = exit_settings['exit_on_signal']


    myobject = Bot(
        name = name,
        quote_asset = quote_asset,
        starting_balance = starting_balance,
        current_balance = starting_balance,
        test_run = test_run
    )

    session.add(myobject)

    entrysets = EntrySettings(
        initial_entry_allocation = initial_entry_allocation,
        signal_distance = signal_distance
        )
    
    exitsets = ExitSettings(
        profit_target = profit_target,      # in %
        stop_loss_value = stop_loss_value,   # in %
        exit_on_signal = exit_on_signal
        )
    myobject.entry_settings = entrysets
    myobject.exit_settings = exitsets
    session.commit()

    for symbol in symbols:
        pair = Pair(
            bot_id = myobject.id,
            symbol = symbol,
            current_order_id = None
        )
        session.add(pair)

    session.commit()


def InitializeDatabaseGridBot(session, params={}):
    """ Function that initializes the database
    by creating a bot with two pairs. """
    name = 'My Bot'
    symbols = []
    quote_asset = 'BTC'
    starting_balance = 0.001
    test_run = False
    initial_entry_allocation = 25
    signal_distance = 0.3
    profit_target = 2
    stop_loss_value = 0
    exit_on_signal = False

    if params.__contains__('name'):
        assert type(params['name']) == str
        name = params['name']

    if params.__contains__('symbols'):
        assert type(params['symbols']) == list
        symbols = params['symbols']

    if params.__contains__('quote_asset'):
        assert type(params['quote_asset']) == str
        quote_asset = params['quote_asset']

    if params.__contains__('starting_balance'):
        assert type(params['starting_balance']) in [int, float]
        starting_balance = params['starting_balance']

    if params.__contains__('test_run'):
        assert type(params['test_run']) == bool
        test_run = params['test_run']

    if params.__contains__('entry_settings'):
        assert type(params['entry_settings']) == dict
        entry_settings = params['entry_settings']
        if entry_settings.__contains__('initial_entry_allocation'):
            assert type(entry_settings['initial_entry_allocation']) in [int, float]
            initial_entry_allocation = entry_settings['initial_entry_allocation']

        if entry_settings.__contains__('signal_distance'):
            assert type(entry_settings['signal_distance']) in [int, float]
            signal_distance = entry_settings['signal_distance']

    if params.__contains__('exit_settings'):
        assert type(params['exit_settings']) == dict
        exit_settings = params['exit_settings']
        if exit_settings.__contains__('take_profit'):
            assert type(exit_settings['take_profit']) in [int, float]
            profit_target = exit_settings['take_profit']

        if exit_settings.__contains__('stop_loss_value'):
            assert type(exit_settings['stop_loss_value']) in [int, float]
            stop_loss_value = exit_settings['stop_loss_value']

        if exit_settings.__contains__('exit_on_signal'):
            assert type(exit_settings['exit_on_signal']) == bool
            exit_on_signal = exit_settings['exit_on_signal']


    myobject = Bot(
        name = name,
        quote_asset = quote_asset,
        starting_balance = starting_balance,
        current_balance = starting_balance,
        test_run = test_run
    )

    session.add(myobject)

    entrysets = EntrySettings(
        initial_entry_allocation = initial_entry_allocation,
        signal_distance = signal_distance
        )
    
    exitsets = ExitSettings(
        profit_target = profit_target,      # in %
        stop_loss_value = stop_loss_value,   # in %
        exit_on_signal = exit_on_signal
        )
    myobject.entry_settings = entrysets
    myobject.exit_settings = exitsets
    session.commit()

    for symbol in symbols:
        pair = Pair(
            bot_id = myobject.id,
            symbol = symbol,
            current_order_id = None
        )
        session.add(pair)

    session.commit()

