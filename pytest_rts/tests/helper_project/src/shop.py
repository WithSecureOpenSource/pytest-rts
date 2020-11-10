
class Shop:

    def __init__(self,item_price,items,money):
        self.item_price = item_price
        self.items = items
        self.money = money

    def buy_item(self):
        if self.items > 0:
            self.items = self.items - 1
            self.money = self.money + self.item_price
        
    def get_items(self):
        return self.items

    def get_item_price(self):
        return self.item_price

    def get_money(self):
        return self.money

    def calculate_useless_stuff(self):
        k = 2
        s = "ATGATATCATCGACGATGTAG"
        context = {}  
        for i,c in enumerate(s):
            if (i+k >= len(s)):break
            substring = s[i:i+k]
            if substring not in context:
                context[substring] = s[i+k]
            else:
                context[substring] = context[substring] + s[i+k]            
    
        return context


    
