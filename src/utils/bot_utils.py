from src.utils.market_utils import best_ask, best_bid, spread, midquote, get_vitals
import numpy as np
import time

from optibook.synchronous_client import Exchange
import logging
from src.utils.logging_utils import initialize_logger

import logging
logger = logging.getLogger("bot_utils")
# Client logger (from optiver)
client_logger = logging.getLogger("client")

initialize_logger(logger, log_name="bot")

#print("Setup was successful.")

def check_price(price):
    max_price = 100
    min_price = 10
    
    return (price < max_price) & (price > min_price)


def cashout():
    e = Exchange()
    a = e.connect()
    
    
    print(e.get_positions())
    
    pos ={'PHILIPS_A': -30, 'PHILIPS_B': 20}
    pos = e.get_positions()
    
    while list(pos.values())!=[0,0]:
        
        for s, p in pos.items():
            price_book = e.get_last_price_book(s)
            # Check market vitals
            try:
                best_ask, best_bid, spread, midquote = get_vitals(price_book)
            except Exception as expt:
                logger.debug(f'Empty price book {expt}')
            #print(best_ask, best_bid, spread, midquote)
            if p > 0:
                volume= min(p, 5)
                price = best_bid
                print(f'{s}, {price}, {volume}, ask')
                if check_price(price):
                    e.insert_order(s, price=price, volume=volume, side='ask', order_type='ioc')
            elif p < 0:
                volume= min(-p, 5)
                price = best_ask
                if check_price(price):
                    e.insert_order(s, price=price, volume=volume, side='bid', order_type='ioc')
                print(f'{s}, {price}, {volume}, bid')
                
        # update pos
        pos = e.get_positions()
        print(f'end: {pos}')
        time.sleep(.01)
    print(e.get_positions())
    
    
if __name__ == '__main__':
    print('print')
    cashout()