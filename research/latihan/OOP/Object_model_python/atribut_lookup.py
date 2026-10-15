""" 
atribut lookup adalah urutan mencari suatu atribut dari suatu object secara berurtan dengan ketentuan python.

data model adalah bagaimana suatu data di baca, ditulis, di update, dan lain sebagainya.

mro (method resulution order) adalah data urutan yang dibaca untuk mencari object. bisa dicari menggunakan __mro__ dari suatu class.
"""

class Order: # class
    diskon: int = 0 # atribut
    def __init__(self, customer): # Object/instance class
        self.customer = customer
        
        
class OrderMember(Order):
    diskon = 10

Andi = OrderMember("Andi")
print(Andi.diskon)

print(OrderMember.__mro__)