from pyjuque.Engine.Models import Base, Bot, Order, Pair, EntrySettings, ExitSettings, getSession

def InitializeDatabase(session, symbols=[], bot_name='My first bot'):
    """ Function that initializes the database
    by creating a bot with two pairs. """
    myobject = Bot(
        name=bot_name,
        quote_asset = 'BTC',
        starting_balance = 0.001,
        current_balance = 0.001,
        test_run=False
    )

    session.add(myobject)

    entrysets = EntrySettings(
        id = 1,
        name ='TimStoploss',
        initial_entry_allocation = 30,
        signal_distance = 1,  # in %
        )
    
    exitsets = ExitSettings(
        id=1,
        name='TimLoss',
        profit_target = 3,      # in %
        stop_loss_value = 10,   # in %
        exit_on_signal=False
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