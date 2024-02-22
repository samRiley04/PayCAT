import payroll as py

a = {"0000":2.5, "0800":1}
b = {"0000":1.25, "0800":1, "1800":1.20}

# a = {"0000":2.5, "0800":1}
# b = {"0000":1.75}

py.blendRatesDicts(a, b, True)