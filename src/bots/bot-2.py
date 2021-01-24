import os
import time
import logging
from optibook.synchronous_client import Exchange
from src.utils.logging_utils import initialize_logger
from src.constants import INSTRUMENTS
 

# 1. --- Set up logging ----
logger = logging.getLogger("bot")
client_logger = logging.getLogger("client")
initialize_logger(logger, log_name="bot2")
initialize_logger(client_logger, log_name="bot2")
logger.info("Logging setup was successful.")


# 2. --- Connect to market ---
e = Exchange()
a = e.connect()


# 3. --- Code components of bot ---
# Inspect current best bids/asks in each excahnge

class trade_logger():
    def __init__(self,env):
        
        self.env = env
        self.positions = env.get_positions()
        self.prev_trades = []
        self.instruments = INSTRUMENTS
        
        for instrument_id in self.instruments:
            trades = self.env.poll_new_trades(instrument_id)
        
        
    def log_trade(self):
        pass
        
def get_spread(instrument_id):
    book = e.get_last_price_book(instrument_id)
    
    best_ask = book.asks[0]
    best_bid = book.bids[0]
    
    spread = best_ask.price - best_bid.price
    
    return best_ask,best_bid,spread

def accumulate():
    
    best_ask_A,best_bid_A,spread_A = get_spread('PHILIPS_A')
    best_ask_B,best_bid_B,spread_B = get_spread('PHILIPS_B')

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
    