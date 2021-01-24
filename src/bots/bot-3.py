
from optibook.synchronous_client import Exchange
import time
import logging
from src.utils.logging_utils import initialize_logger
import os 
import numpy as np
# 1. --- Set up logging ----
# Bot logger
logger = logging.getLogger("bot3")
# Client logger (from optiver)
client_logger = logging.getLogger("client")

initialize_logger(logger, log_name="bot1")
initialize_logger(client_logger, log_name="bot1")

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
        self.instruments = ["PHILIPS_A","PHILIPS_B"]
        
        for instrument_id in self.instruments:
            trades = self.env.poll_new_trades(instrument_id)
        
        
    def log_trade(self):
        return
        


def get_spread(instrument_id):
    book = e.get_last_price_book(instrument_id)
    
    best_ask = book.asks[0]
    best_bid = book.bids[0]
    
    spread = best_ask.price - best_bid.price
    
    return best_ask,best_bid,spread

def spread(best_ask, best_bid):
    return best_ask - best_bid

def midquote(best_ask, best_bid):
    return 0.5 * (best_ask - best_bid)
    
instruments = ["PHILIPS_A","PHILIPS_B"]

def accumulate():
    
    best_ask_A,best_bid_A,spread_A = get_spread('PHILIPS_A')
    best_ask_B,best_bid_B,spread_B = get_spread('PHILIPS_B')
    
    DeltaA = best_bid_B.price - best_ask_A.price
    DeltaB = best_bid_A.price - best_ask_B.price
    
    # Is there reason to arbitrage
    if (DeltaA > 0) or (DeltaB > 0):
        
        logger.info(f'Arbitrage')
    
        if DeltaA > 0:
            delta = DeltaA
            bbid = best_bid_B
            bask = best_ask_A
            ibuy, isell = 'PHILIPS_A', 'PHILIPS_B'
            
        elif DeltaB > 0:
            
            delta = DeltaA
            bbid = best_bid_B
            bask = best_ask_A
            ibuy, isell = 'PHILIPS_B', 'PHILIPS_A'
        
        
        max_volume = 30
        
        positions = e.get_positions()
        winded = (positions[ibuy] -positions[isell])/1000
        
        paramb = 0.5
        #max_volume =  max_volume * round( (-np.sin(winded * np.pi/2) + .5)**(paramb/delta))
        volume = min([bbid.price,bask.price,max_volume])
        
        logger.info('Volume: {}'.format(volume))
        
        try:
            # First I want to buy B at the price quoted 
            buy = e.insert_order(ibuy, price=bask.price, volume=volume, side='bid', order_type='ioc')
            #logger.info('Trade Succeeded sell: volume {}'.format(volume))
            
            trades = e.poll_new_trades(ibuy)
            vol_bought = 0
            # Check trade went through
            if len(trades)>0:
                # Find out exact valume of successful trade
                for t in trades:
                    if t.order_id == buy:
                        vol_bought = t.volume
                        
                sell = e.insert_order(isell, price=bbid.price, volume=vol_bought, side='ask', order_type='ioc')
            #logger.info('Trade Succeeded buy: volume {}'.format(volume))
            
        except Exception as expt:
            logger.info('Buy order failed - too slow? {}'.format(expt))
            
    else:
        #pass
        logger.info(f'No arbitrage')
        
        
   
            
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
            #print(1)
            accumulate()
        dissapate()
        time.sleep(0.001)
        '''
        for instrument_id in instruments:
            outstanding = e.get_outstanding_orders(instrument_id)
            for o in outstanding.values():
                print(f"Outstanding order: order_id({o.order_id}), instrument_id({o.instrument_id}), price({o.price}), volume({o.volume}), side({o.side})")
        '''
    except Exception as expt:
            if type(expt).__name__ == 'IndexError':
                logger.info('Main Error {}'.format(expt))
            else:
                logger.info('Main Error {}'.format(expt))
    