class Test:
    def __init__(self):
        self.data = []


var = Test()
var2 = Test()

var.data.append(10)
var2.data.append(20)

print(var.data,var2.data)