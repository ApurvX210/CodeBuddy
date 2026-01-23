class Test:
    a = {}
    b = 10


var = Test()
var2 = Test()

var.a[10] = 20
var.b = 20

print(var.a,var.b)
print(var2.a,var2.b)