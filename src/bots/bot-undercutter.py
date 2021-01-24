import os
import time
import logging
from optibook.synchronous_client import Exchange
from src.utils.logging_utils import initialize_logger
from src.constants import INSTRUMENTS
from src.utils.market_utils import best_ask, best_bid, spread, midquote, get_vitals
from src.utils.inventory_utils import PendingOrders
 
# TUNING PARAMETERS:
UNDERCUT_FACTOR = 0.8

# 1. --- Set up logging ----
logger = logging.getLogger("bot")
client_logger = logging.getLogger("client")
initialize_logger(logger, log_name="undercutter-bot")
initialize_logger(client_logger, log_name="undercutter-bot")
logger.info("Logging setup was successful.")


# 2. --- Connect to market ---
e = Exchange()
a = e.connect()

# 3. --- Define undercutter loop
    # While True

our_orders = PendingOrders(exchange=e)

def calculate_bid_and_ask(market_spread, market_midquote, undercut_factor = 0.8):
    """Calculate quote bid and ask values from current market spread and value"""
            
    bid = market_midquote - (0.5 * market_spread * undercut_factor)
    ask = market_midquote + (0.5 * market_spread * undercut_factor)
            
    return bid, ask

def undercutter_loop():
    
    # Update info
    our_orders.update()
    logger.debug("Updating PendingOrders")
    
    positions = e.get_postions()
    
    for instrument_id in INSTRUMENTS:
        price_book = e.get_last_price_book(instrument_id)
        
        # Check market vitals
        best_ask, best_bid, spread, midquote = get_vitals(price_book)
        
        our_bid_is_best = False
        if our_orders.highest_bid(instrument_id) == best_bid:  # in case of no bid: None (which equals false)
            logger.info("Our bid is highest")
            our_bid_is_best = True
        our_ask_is_best = False
        if our_orders.lowest_ask(instrument_id) == best_ask:   # in case of no bid: None (which equals false)
            logger.info("Our ask is highest")
            our_ask_is_best = True
            
        # Calculate bid and ask prices 
        
        bid_price, ask_price = calculate_bid_and_ask(spread,midquote,undercut_factor=UNDERCUT_FACTOR)
        logger.info(f"Using ask-price {ask_price} and bid-price {bid_price} for undercutting.")
        
        #####################
        volume = 20         #
        #####################
        
        our_bid_id = our_orders.highest_bid_id(instrument_id)
        our_ask_id = our_orders.lowest_ask_id(instrument_id)
        
        # Check our positions
        
        position = positions[instrument_id]
        logger.info(position)
        max_position = 250
        
        
        if not our_bid_is_best:
            # Delete order if already is one, then place new
            if our_bid_id is not None:
                logger.info(f"Deleting bid {our_bid_id}")
                delete = e.delete_order(instrument_id, order_id=our_bid_id)
            logger.info(f"Ordering bid at {bid_price} for {instrument_id}")
            if position < max_position:
                e.insert_order(instrument_id, price=bid_price, volume=volume, side="bid", order_type="limit")
        else:
            # keep it that way
            logger.debug("Our bid is best")
            pass
        
        if not our_ask_is_best:
            # Delete order if already is one, then place new
            if our_ask_id is not None:
                delete = e.delete_order(instrument_id, order_id=our_ask_id)
                logger.info(f"Deleting ask {our_ask_id}")
            logger.info(f"Ordering ask at {ask_price} for {instrument_id}")
            if position > (-max_position):
                e.insert_order(instrument_id, price=ask_price, volume=volume, side="ask", order_type="limit")
        else:
            # keep it that way
            logger.debug("Our ask is best")
            pass
    
    # If we don't have any order in the book:
        # add new quote 
    # If we have one order (basically we made a trade):
        # wait for order execution time (2/20 s ?)
        # if execution time is surpassed:
            # cancel the trade 
            # add new quote
    # If we have two orders (bid & ask):
        # wait for quote time
        # if quote time is surpassed
            # add new quote
            
    # NEEDS:
        # 1. Checking for market vitals
        
        # 2. Checking for inventory vitals
            
        # 3. Determining a good bid & ask value depending on 
                # - our inventoy
                # - the current market spread
                # - the spread in the other market
            
        # 4. Actually quoting the bid

    
start = time.time()        
try:
    accumulate()
except:
    pass
end = time.time()

logger.info(f'Took {(end-start)*1e3} ms')

def check_positions():
        
    positions = e.get_positions()
    vol_positions = [abs(positions[p]) for p in positions]
    max_vol = max(vol_positions)
        
    return (max_vol < 200)

# 4. --- Start up bot ---

logger.info(f'initial pnl {e.get_pnl()}')
while True:
    try:
        '''
        for instrument_id in instruments:
            trades = e.poll_new_trades(instrument_id)
        if check_positions():
            accumulate()
        dissapate()
        '''
        time.sleep(0.5)
        undercutter_loop()
        '''
        for instrument_id in instruments:
            outstanding = e.get_outstanding_orders(instrument_id)
            for o in outstanding.values():
                print(f"Outstanding order: order_id({o.order_id}), instrument_id({o.instrument_id}), price({o.price}), volume({o.volume}), side({o.side})")
        '''
    except:
        pass

logger.info(f'final pnl {e.get_pnl()}')