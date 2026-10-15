""" 
properti dan invariation ini berguna untuk mendefine data model.
prperti ini mendefinisiakn suatu atribut sebagai suatu yang bisa di modifikasi
invariation memastikan atribut sesuai dengan aturannya
"""


class Order:
    diskon = 0 
    def __init__(self, customer, income, table_number):
        self.customer = customer
        self.income = income
        self.order_item = []
        self.table_number = table_number
        
    @property
    def table_number(self):
        return self._table_number
    
    @table_number.setter
    def table_number(self, number):
        if number <= 0:
            raise ValueError("number of table must be > 0")
        self._self_number = number
        

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
    andi = OrderMember("Andi", 1000, 2)
    andi.order_item.append("kopi")
    
    sinta = OrderMember("sinta", 2000, 1)
    sinta.order_item.append("nasi goreng")
    print("order andi: ", andi.order_item)
    print("order sinta: ", sinta.order_item)
    
    print(andi.diskon)
    print(sinta.diskon)

    
    print(andi)
    print(sinta)
    print("jumlah: ", andi + sinta)
    print("order sama: ", andi == sinta)
    print("hash key andi: ", hash(andi))
    
    sinta.table_number = -2
    
    