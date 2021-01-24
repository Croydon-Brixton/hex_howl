from src.constants import INSTRUMENTS

class PendingOrders:
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
        """Update the pending orders"""
        for instrument in INSTRUMENTS:
            self.orders = list(self.exchange.get_outstanding_orders(instrument).values())
            self.asks[instrument] = sorted([order for order in self.orders if order.side == "ask"], key = lambda x: x.price)
            self.bids[instrument] = sorted([order for order in self.orders if order.side == "bid"], key = lambda x: x.price)
    
    def highest_bid(self, instrument: str):
        bids = self.bids[instrument]
        if len(bids) > 0:
            return bids[-1].price
        else: 
            return None
        
    def highest_bid_id(self, instrument: str):
        bids = self.bids[instrument]
        if len(bids) > 0:
            return bids[-1].order_id
        else: 
            return None
            
    def lowest_ask(self, instrument: str):
        asks = self.asks[instrument]
        if len(asks) > 0:
            return asks[0].price
        else: 
            return None
        
    def lowest_ask_id(self, instrument: str):
        asks = self.asks[instrument]
        if len(asks) > 0:
            return asks[0].order_id
        else: 
            return None
    
    def spread(self,instrument: str):
        lowest_ask = self.lowest_ask(instrument)
        highest_bid = self.highest_bid(instrument)
        if not lowest_ask or highest_bid:
            return None
        return self.lowest_ask(instrument) - self.highest_bid(instrument)
    
    def volume_ask(self, instrument):
        return sum([order.volume for order in self.asks[instrument]])
        
    def volume_bid(self, instrument):
        return sum([order.volume for order in self.bids[instrument]])
        
    def orders_in_last_20ms(self):
        pass