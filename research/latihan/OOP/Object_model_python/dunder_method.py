""" 
dunder method memungkinkan untuk melakukan operasi terhadap atribut
"""



class Order:
    diskon = 0 
    def __init__(self, customer, income):
        self.customer = customer
        self.income = income
        self.order_item = []
        
    def __repr__(self):
        return f"customer : {self.customer} \nincome : {self.income}"
        
    def __add__(self, other):
        if not isinstance(other, Order):
            return NotImplemented
        return self.income + other.income
        
    def __eq__(self, value):
        if not isinstance(value, Order):
            return NotImplemented
        return self.order_item == value.order_item
    
    def __hash__(self):
        return hash(self.income)
    
    
        
class OrderMember(Order):
    diskon = 10
    
    
if __name__ == "__main__":
    andi = OrderMember("Andi", 1000)
    andi.order_item.append("kopi")
    
    sinta = OrderMember("sinta", 2000)
    sinta.order_item.append("nasi goreng")
    print(andi.order_item)
    print(sinta.order_item)
    
    print(andi.diskon)
    print(sinta.diskon)
    
    
    print(andi)
    print(sinta)
    print("jumlah: ", andi + sinta)
    print("order sama: ", andi == sinta)
    print(hash(andi))
    