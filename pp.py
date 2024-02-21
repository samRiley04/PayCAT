from decimal import *

getcontext().prec = 12
getcontext().rounding = ROUND_HALF_DOWN

FOURPLACES = Decimal(10) ** -4
EIGHTPLACES = Decimal(10) ** -8

A = Decimal(40.068)
B = Decimal(0.25)
C = Decimal(0.12345)

g = A*B
# print(A)
# print(B)

print(C)
print(C.quantize(EIGHTPLACES, rounding=ROUND_HALF_DOWN).quantize(FOURPLACES, rounding=ROUND_HALF_DOWN))
print(C.quantize(FOURPLACES, rounding=ROUND_HALF_DOWN))
