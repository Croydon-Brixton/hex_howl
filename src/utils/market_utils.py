def best_ask(book):
    """Return best ask of a book"""
    return book.asks[0].price
    
def best_bid(book):
    """Return best bid of a book"""
    return book.bids[0].price

def spread(book):
    """Return spread of a book"""
    return best_ask(book) - best_bid(book)

def midquote(book):
    """Return midquote of a book"""
    return 0.5 * (best_ask(book) + best_bid(book))
    
def get_vitals(book):
    """Return vital signs of a book"""
    return best_ask(book), best_bid(book), spread(book),midquote(book)
    