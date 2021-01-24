import os
import time
import logging
import time
from optibook.synchronous_client import Exchange
from src.utils.logging_utils import initialize_logger
from src.constants import INSTRUMENTS
from src.utils.market_utils import best_ask, best_bid, spread, midquote, get_vitals
from src.utils.inventory_utils import PendingOrders
import math
import numpy as np
 
# TUNING PARAMETERS:
UNDERCUT_FACTOR = 0.8 # maximally undercut illiquid market by this value (1 = no undercutting)
MAX_VOLUME = 30  # maximally offer this volume for trade at once
VOL_SCALE_PARAM = 0.5 # Sign ** VOL_SCALE_PARAM/ Ddelta
QUOTE_TIME_LIMIT = 0.1 # in s

# 1. --- Set up logging ----
logger = logging.getLogger("bot")
client_logger = logging.getLogger("client")
initialize_logger(logger, log_name="liquidifier-bot")
initialize_logger(client_logger, log_name="liquidifier-bot")
logger.info("Logging setup was successful.")

# 2. --- Connect to market ---
e = Exchange()
a = e.connect()
our_orders = PendingOrders(exchange=e)

# 3. --- Define price setting functions ---
def calculate_undercut_price(market_spread, market_midquote, undercut_factor = UNDERCUT_FACTOR):
    """Calculate quote bid and ask values from current market spread and value"""
    bid = market_midquote - (0.5 * market_spread * undercut_factor)
    ask = market_midquote + (0.5 * market_spread * undercut_factor)
            
    return bid, ask
    
def calculate_ask_price(best_ask_A, best_ask_B, undercut_ask_B):
    """Calculate ask price for quote on illiquid market B"""
    if best_ask_A >= best_ask_B:
        next_ask_B = best_ask_A
        logger.info(f"Ask price B pinned to {next_ask_B} vs {best_ask_B}")
    else:
        mean_AB = 0.5*(best_ask_A + best_ask_B)
        next_ask_B = max(undercut_ask_B, mean_AB)
        logger.info(f"Ask price B undercut to {next_ask_B} vs {best_ask_B}")
    return next_ask_B
        
def calculate_bid_price(best_bid_A, best_bid_B, undercut_bid_B):
    """Calculate the bid price for quote on illiquid market B""" 
    if best_bid_A > best_bid_B:
        mean_AB = 0.5*(best_bid_A + best_bid_B)
        next_bid_B = min(undercut_bid_B, mean_AB)
        logger.info(f"Bid price B undercut (raised) to {next_bid_B} vs {best_bid_B}")
    else:
        next_bid_B = best_bid_A
        logger.info(f"Bid price B pinned to {next_bid_B} vs {best_bid_B}")
    return next_bid_B
        
# 4. --- Define volume setting functions ---        
def calculate_ask_vol_B(delta_from_ask_B, inventory_A, inventory_B):
    ''' Calcululate volume of ask (we are buying A and sellig B) '''
    
    # Case: We are buying A and selling B
    winding = (inventory_A - inventory_B)/1000  # -1 (Not invested in A)  to 1 (INVESTED IN A)  # TO DO
    delta_from_ask_B = delta_from_ask_B +0.001
    vol = np.round( MAX_VOLUME * (-np.sin(winding * np.pi/2)/2 + .5)**(VOL_SCALE_PARAM/(delta_from_ask_B)))
    
    return vol

def calculate_bid_vol_B(delta_from_bid_B, inventory_A, inventory_B):
    ''' Calcululate volume of bid (we are buying B and selling A) '''
    
    # Case: We are buying B and selling A
    winding = (inventory_B - inventory_A)/1000  # -1 to 1
    delta_from_ask_B = delta_from_ask_B +0.001
    vol = np.round( MAX_VOLUME * (-np.sin(winding * np.pi/2)/2 + .5)**(VOL_SCALE_PARAM/delta_from_bid_B))
    
    return vol

def calculate_quote(e):
    """Calculate prices and volumes for our quote in illiquid market"""
    # PRICE SETTING FOR ILLIQUID MARKET
    # Asumption: A is liquid market, B is illiquid.
    price_book_A, price_book_B = [e.get_last_price_book(instrument_id) for instrument_id in INSTRUMENTS]
    # Get market vitals
    best_ask_A, best_bid_A, spread_A, midquote_A = get_vitals(price_book_A)
    best_ask_B, best_bid_B, spread_B, midquote_B = get_vitals(price_book_B)
    # Calculate undercutting prices for illiquid market B
    undercut_bid_B, undercut_ask_B = calculate_undercut_price(spread_B, midquote_B, UNDERCUT_FACTOR)
    # Calculate next bid and ask on illiquid market
    next_ask_B = calculate_ask_price(best_ask_A, best_ask_B, undercut_ask_B)
    next_bid_B = calculate_bid_price(best_bid_A, best_bid_B, undercut_bid_B)
    # Calculate cross-market spreads we're making
    delta_from_bid_B = best_bid_A - next_bid_B  # we sell at A and buy at B
    delta_from_ask_B = best_ask_B - best_ask_A  # we buy at A and sell at B
    # Sanity check that we never offer a negative delta trade for us
    assert delta_from_bid_B >= 0, f"Negative delta from bid B: {delta_from_bid_B}"
    assert delta_from_ask_B >= 0, f"Negative delta from ask B: {delta_from_ask_B}"
    
    # VOLUME SETTING
    # inventory_A/B will be between -/+ 500
    inventory_A, inventory_B = [e.get_positions()[instrument_id] for instrument_id in INSTRUMENTS] 
    # Case 1: We are buying A and selling B
    next_vol_ask_B = calculate_ask_vol_B(delta_from_ask_B, inventory_A, inventory_B)
    # Case 2: We are buying B and selling A
    next_vol_bid_B = calculate_bid_vol_B(delta_from_bid_B, inventory_A, inventory_B)
    # Sanity check that volumes are within 0 and MAX_VOLUME
    assert 0 <= next_vol_ask_B <= MAX_VOLUME, f"Volume larger than max Volume for ask B"
    assert 0 <= next_vol_bid_B <= MAX_VOLUME, f"Volume larger than max volume for bid B"
    
    return next_ask_B, next_vol_ask_B, next_bid_B, next_vol_bid_B
    
# 5. --- Put Bot together ---  
def market_making_loop():
    
    ask_timestamp = time.time()
    bid_timestamp = time.time()
    
    while True:
        # UPDATING BID
        next_ask_B, next_vol_ask_B, next_bid_B, next_vol_bid_B = calculate_quote(e)
        
        # UPDATING QUOTES
        our_orders.update()
        our_bid_id = our_orders.highest_bid_id("PHILIPS_B")
        our_ask_id = our_orders.lowest_ask_id("PHILIPS_B")
        
        ask_has_expired = time.time() - ask_timestamp > QUOTE_TIME_LIMIT
        ask_was_fulfilled = our_ask_id is None
        if ask_was_fulfilled and next_vol_ask_B > 0:
            # Enter new ask
            e.insert_order("PHILIPS_B", price=next_ask_B, volume=next_vol_ask_B, side="ask", order_type="limit")
            ask_timestamp = time.time()
        elif ask_has_expired and next_vol_ask_B > 0:
            # Update current ask
            logger.info(f"Deleting bid {our_ask_id}")
            delete = e.delete_order("PHILIPS_B", order_id=our_ask_id)
            e.insert_order("PHILIPS_B", price=next_ask_B, volume=next_vol_ask_B, side="ask", order_type="limit")
            ask_timestamp = time.time()
        else:
            # just wait
            pass
        
        bid_has_expired = time.time() - bid_timestamp > QUOTE_TIME_LIMIT
        bid_was_fulfilled = our_bid_id is None
        if bid_was_fulfilled and next_vol_bid_B > 0:
            # Enter new bid
            e.insert_order("PHILIPS_B", price=next_bid_B, volume=next_vol_bid_B, side="bid", order_type="limit")
            bid_timestamp = time.time()
        elif bid_has_expired and next_vol_bid_B > 0:
            # Update current bid
            logger.info(f"Deleting bid {our_bid_id}")
            delete = e.delete_order("PHILIPS_B", order_id=our_bid_id)
            e.insert_order("PHILIPS_B", price=next_bid_B, volume=next_vol_bid_B, side="bid", order_type="limit")
            bid_timestamp = time.time()
        else:
            # just wait
            pass
        
        # EQUILIBRATE INVENTORY (HEDGING):
        # Soft hedging
        dissipate()
    
        
def dissipate():
    """Hedge our positions softly"""
    
    # See how hedged we are
    pos = e.get_positions()
    pos_diff = pos['PHILIPS_A'] + pos['PHILIPS_B'] # Get total position 

    # Get market info for A
    price_book = e.get_last_price_book('PHILIPS_A')
    best_ask, best_bid, spread, midquote = get_vitals(price_book) # always buy or sell in A

    if pos_diff > 0: # more in A, get rid of a
        side, price = 'ask', best_bid
        logger.info(f'More in A {pos_diff}, getting rid {pos}')
    elif pos_diff < 0: # less in A, buy A
        side, price = 'bid', best_ask
        logger.info(f'Less in A {pos_diff}, buying {pos}')
    else:
        return True  # Don't place any orders

    volume = abs(pos_diff)
    #logger.debug(f'side : {side}, volume: {volume}, price {price}')
    
    e.insert_order('PHILIPS_A', price=price, volume=volume, side=side, order_type='ioc')
    return False
    
    
if __name__ == "__main__":
    
    while True:
        try:
            market_making_loop()
        except Exception as expt:
            logger.info('Exception in Main {}'.format(expt))
            #pass
    