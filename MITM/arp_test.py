from scapy.all import *

conf.iface = r"\Device\NPF_{DD9E91FC-B952-44D5-9394-795A6DF2C164}"

ip = "192.168.0.1"

pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)

ans = srp(pkt, timeout=3, verbose=False)[0]

print(ans)

for s, r in ans:
    print("IP:", r.psrc)
    print("MAC:", r.hwsrc)