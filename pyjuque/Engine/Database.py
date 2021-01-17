from pyjuque.Engine.Models import Base, TABot as Bot, Pair, EntrySettings, ExitSettings, getSession

def InitializeDatabase(session, params={}):
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
        name = params['name']

    if params.__contains__('symbols'):
        symbols = params['symbols']

    if params.__contains__('quote_asset'):
        quote_asset = params['quote_asset']

    if params.__contains__('starting_balance'):
        starting_balance = params['starting_balance']

    if params.__contains__('test_run'):
        test_run = params['test_run']

    if params.__contains__('initial_entry_allocation'):
        initial_entry_allocation = params['initial_entry_allocation']

    if params.__contains__('signal_distance'):
        signal_distance = params['signal_distance']

    if params.__contains__('profit_target'):
        profit_target = params['profit_target']

    if params.__contains__('stop_loss_value'):
        stop_loss_value = params['stop_loss_value']

    if params.__contains__('exit_on_signal'):
        exit_on_signal = params['exit_on_signal']


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