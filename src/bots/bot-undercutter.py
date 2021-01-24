import os
import time
import logging
from optibook.synchronous_client import Exchange
from src.utils.logging_utils import initialize_logger
from src.constants import INSTRUMENTS
from src.utils.market_utils import best_ask, best_bid, spread, midquote, get_vitals
from src.utils.inventory_utils import Inventory
 
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

inventory = Inventory(exchange=e)

def undercutter_loop():
    
    # Update info
    inventory.update()
    
    for instrument_id in INSTRUMENTS:
        price_book = e.get_last_price_book(instrument_id)
    
        # Check market vitals
        best_ask, best_bid, spread, midquote = get_vitals(price_book)
        
        our_bid_is_best = False
        if inventory.highest_bid(instrument_id) == best_bid:  # in case of no bid: None (which equals false)
            our_bid_is_best = True
        our_ask_is_best = False
        if inventory.lowest_ask(instrument_id) == best_ask:   # in case of no bid: None (which equals false)
            our_ask_is_best = True
            
        # Calculate bid and ask prices 
        
        bid, ask = calculate_bid_and_ask(spread,midquote,undercut_factor=UNDERCUT_FACTOR)
            
        if not our_ask_is_best:
            # amend an order
            
            # update
            pass
        else:
            # keep it that way
            pass
        
        if not our_bid_is_best:
            # update
            pass
        else:
            # keep it that way
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
        def calculate_bid_and_ask(market_spread, market_midquote, undercut_factor = 0.8):
            """Calculate quote bid and ask values from current market spread and value"""
            
            bid = market_midquote - market_spread * undercut_factor
            ask = market_midquote + market_spread * undercut_factor
            
            return bid, ask
            
        # 4. Actually quoting the bid
        def insert_quote(instrument, bid_price, ask_price, volume):
            e.insert_order(instrument, price=bid_price, volume=volume, side="bid", order_type="limit")
            e.insert_order(instrument, price=ask_price, volume=volume, side="ask", order_type="limit")
            
        def insert_decaying_quote():
            pass
    
   
##### FOR COPY PASTING #### 
def accumulate():
    
    book_A, book_B = [e.get_last_price_book(instrument) for instrument in INSTRUMENTS]
    best_ask_A, best_bid_A, spread_A = get_vitals(book_A)
    best_ask_B, best_bid_B, spread_B = get_vitals(book_B)
    # Check for ovelap and place order A
    if best_ask_B.price < best_bid_A.price:

        #volume = 1 #edit later to min volume if works
        max_volume = 50
        
        volume = min([best_ask_B.volume,best_bid_A.volume,max_volume])
        try:
            # First I want to buy B at the price quoted 
            buy_B = e.insert_order("PHILIPS_B", price=best_ask_B.price, volume=volume, side='bid', order_type='ioc')
            trades = e.poll_new_trades("PHILIPS_B")
            vol_bought = 0
            # Check trade went through
            if len(trades)>0:
                # Find out exact valume of successful trade
                vol_bought = trades[0].volume
                # Then I want to sell at A at the price expected but also set up limit order ask on B so we can get rid
                # of accumulated stock at higher price
                sell_A = e.insert_order("PHILIPS_A", price=best_bid_A.price, volume=vol_bought, side='ask', order_type='ioc')
                
                sell_B = e.insert_order("PHILIPS_B", price=(best_ask_B.price*1.01), volume=vol_bought, side='ask', order_type='limit')
                print('placed balancing sell')
                # Check success of ioc sale and set up by back for cheaper
                trades = e.poll_new_trades("PHILIPS_A")
                if len(trades)>0:
                    vol_bought = trades[0].volume
                    buy_A = e.insert_order("PHILIPS_A", price=best_bid_A.price*0.99, volume=vol_bought, side='bid', order_type='limit')
                    print('placed balancing buy')
            
            logger.info(f'Trade succeeded: {volume} B->A')
        except:
            logger.info('Buy order failed - too slow?')

    # Check for ovelap and place order A
    if best_ask_A.price < best_bid_B.price:

        #volume = 1 #edit later to min volume if works
        volume = min([best_ask_A.volume,best_bid_B.volume,max_volume])
        try:
            buy_A = e.insert_order("PHILIPS_A", price=best_ask_A.price, volume=volume, side='bid', order_type='ioc')
            sell_B = e.insert_order("PHILIPS_B", price=best_bid_B.price, volume=volume, side='ask', order_type='ioc')
            
            buy_A = e.insert_order("PHILIPS_A", price=best_ask_A.price, volume=volume, side='bid', order_type='ioc')
            trades = e.poll_new_trades("PHILIPS_A")
            vol_bought = 0
            if len(trades)>0:
                vol_bought = trades[0].volume
                sell_B = e.insert_order("PHILIPS_B", price=best_bid_B.price, volume=vol_bought, side='ask', order_type='ioc')
                sell_A = e.insert_order("PHILIPS_A", price=(best_ask_A.price*1.01), volume=vol_bought, side='ask', order_type='limit')
                print('placed balancing sell')
                trades = e.poll_new_trades("PHILIPS_B")
                if len(trades)>0:
                    vol_bought = trades[0].volume
                    buy_B = e.insert_order("PHILIPS_B", price=best_bid_B.price*0.99, volume=vol_bought, side='bid', order_type='limit')
                    print('placed balancing buy')
                    
            logger.info(f'Trade succeeded: {volume} A->B')
        except:
            logger.info('Buy order failed - too slow?')
            
    return

def dissapate():
    return 
    
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
while True:
    try:
        for instrument_id in instruments:
            trades = e.poll_new_trades(instrument_id)
        if check_positions():
            accumulate()
        dissapate()
        '''
        for instrument_id in instruments:
            outstanding = e.get_outstanding_orders(instrument_id)
            for o in outstanding.values():
                print(f"Outstanding order: order_id({o.order_id}), instrument_id({o.instrument_id}), price({o.price}), volume({o.volume}), side({o.side})")
        '''
    except:
        pass
    