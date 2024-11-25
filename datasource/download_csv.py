from Ashare import *

target = 'sh000001' 
fq = "1d"
count = 10
df = get_price(target, frequency=fq, count=count)
print("raw")
print(df.head())

file = target + '.csv'

if fq != "1d":
    raise TypeError("frequency type: " + fq + " not implemented")

header = ["datetime","open", "high", "low", "close", "volume"]
df.reset_index(inplace=True)
df.columns = header

print("processed")
print(df.head())
df.to_csv(file, header=header, index=False)