from src.constants import INSTRUMENTS

class Inventory:
    def __init__(self, exchange):
        
        self.exchange = exchange
        self.orders = {}
        self.bids = {}
        self.asks = {}
        self.update() 
        
    @staticmethod
    def _order_to_dict(order):
        return {"id" : order.order_id, "price": order.price, "volume": order.volume, "instrument": order.instrument_id}
        
    def update(self):
        
        for instrument in INSTRUMENTS:
            self.orders = list(self.exchange.get_outstanding_orders(instrument).values())
            self.asks[instrument] = sorted([order for order in self.orders if order.side == "ask"], key = x["price"])
            self.bids[instrument] = sorted([order for order in self.orders if order.side == "bid"], key = x["price"])
           
        
        self.orders = {instrument: list(self.exchange.get_outstanding_orders(instrument).values()) for instrument in INSTRUMENTS } 
    
    def highest_bid(self, instrument: str):
        prices = [order.price for order in self.orders[instrument] if order.side == 'bid']
        if len(prices) == 0:
            return None
        return max(prices)
        
    def highest_bid_id(self, instrument: str):
        prices = [order.prices for order in self.orders[instrument] if order.side == 'bid']
        if len(prices) == 0:
            return None
        return max(prices)
        
    def lowest_ask(self, instrument: str):
        prices = [order.price for order in self.orders[instrument] if order.side == 'ask']
        if len(prices) == 0:
            return None
        return min(prices)
        
    def lowest_ask_id(self, instrument: str):
        
    
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