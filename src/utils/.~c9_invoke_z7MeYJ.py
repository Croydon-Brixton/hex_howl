from src.constants import INSTRUMENTS

class I:
    def __init__(self, exchange):
        
        self.exchange = exchange
        self.orders = None # current orders
        self.update() 
        
    @staticmethod
    def _order_to_dict(order):
        return {"id" : order.order_id, "price": order.price, "volume": order.volume, "instrument": order.instrument_id}
        
    def update(self):
        self.orders = {instrument: list(self.exchange.get_outstanding_orders(instrument).values()) for instrument in INSTRUMENTS } 
    
    def highest_bid(self, instrument: str):
        prices = [order.price for order in self.orders[instrument] if order.side == 'bid']
        if len(prices) == 0:
            return None
        return max(prices)
        
    def lowest_ask(self, instrument: str):
        prices = [order.price for order in self.orders[instrument] if order.side == 'ask']
        if len(prices) == 0:
            return None
        return min(prices)
    
    def spread(self,instrument: str):
        lowest_ask = self.lowest_ask(instrument)
        highest_bid = self.highest_bid(instrument)
        if not lowest_ask or highest_bid:
            return None
        return self.lowest_ask(instrument) - self.highest_bid(instrument)
    
    def volume_ask(self, instrument):
        return sum([order.volume for order in self.orders[instrument] if order.side == 'ask'])
        
    def volume_bid(self, instrument):
        return sum([order.volume for order in self.orders[instrument] if order.side == 'bid'])
        
    def orders_in_last_20ms(self):
        pass