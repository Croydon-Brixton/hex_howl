from src.constants import INSTRUMENTS

class OrderBook:
    
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
        return max(prices)
        
    def lowest_ask(self, instrument: str):
        prices = [order.price for order in self.orders[instrument] if order.side == 'ask']
        return min(prices)
    
    def spread(self,instrument: str):
        return self.lowest_ask(instrument) - self.highest_bid(instrument)
    
    def balance(self, instrument: str):
        pass
        
    def orders_in_last_20ms(self):
        
    
        self.orders_in_last_timeframe 
        pass