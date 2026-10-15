""" 
class atribut berguna agar atribut yang di definisikan tidak dipakai untuk global sehingga setiap atribut yang digunakan unique.
"""

class Order:
    diskon = 0 
    def __init__(self, customer):
        self.customer = customer
        self.order_item = []
        
        
class OrderMember(Order):
    diskon = 10
    
    
if __name__ == "__main__":
    andi = OrderMember("Andi")
    andi.order_item.append("kopi")
    
    sinta = OrderMember("sinta")
    sinta.order_item.append("nasi goreng")
    print(andi.order_item)
    print(sinta.order_item)
    
    print(andi.diskon)
    print(sinta.diskon)
