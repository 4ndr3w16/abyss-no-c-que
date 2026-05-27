from scapy.all import *

print("IFACE ACTUAL:")
print(conf.iface)

print("\nLISTA:")
for i in get_if_list():
    print(i)