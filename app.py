import os
import subprocess
import socket
import dns.resolver
import re
import platform
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Configurable port list — extend this to add more services anytime
# ---------------------------------------------------------------------------
DEFAULT_PORTS = [
    {"port": 21,   "service": "FTP"},
    {"port": 22,   "service": "SSH"},
    {"port": 25,   "service": "SMTP"},
    {"port": 53,   "service": "DNS"},
    {"port": 80,   "service": "HTTP"},
    {"port": 110,  "service": "POP3"},
    {"port": 143,  "service": "IMAP"},
    {"port": 443,  "service": "HTTPS"},
    {"port": 3306, "service": "MySQL"},
    {"port": 3389, "service": "RDP"},
    {"port": 5432, "service": "PostgreSQL"},
    {"port": 8080, "service": "HTTP-Alt"},
]


# ---------------------------------------------------------------------------
# Ping
# ---------------------------------------------------------------------------
def run_ping(host: str) -> dict:
    """
    Send 4 ICMP packets using the OS ping command.
    Works on Linux (Railway) and Windows.
    """
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "4", host]
    else:
        cmd = ["ping", "-c", "4", "-W", "3", host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        output = result.stdout + result.stderr

        # Parse packet loss
        loss_match = re.search(r"(\d+)%\s+packet loss", output)
        packet_loss = int(loss_match.group(1)) if loss_match else 100

        # Parse average round-trip time
        # Linux:   rtt min/avg/max/mdev = 1.2/5.4/9.1/...
        # Windows: Minimum = Xms, Maximum = Xms, Average = Xms
        rtt_match = re.search(r"(?:avg|Average)\s*[=\/]\s*([\d.]+)", output)
        if not rtt_match:
            rtt_match = re.search(r"[\d.]+\/([\d.]+)\/[\d.]+", output)

        response_time = round(float(rtt_match.group(1))) if rtt_match else 0

        status = "online" if packet_loss < 100 else "offline"
        return {
            "status": status,
            "responseTime": response_time,
            "packetLoss": packet_loss,
        }

    except subprocess.TimeoutExpired:
        return {"status": "offline", "responseTime": 0, "packetLoss": 100}
    except Exception as e:
        return {"status": "offline", "responseTime": 0, "packetLoss": 100}


# ---------------------------------------------------------------------------
# Traceroute
# ---------------------------------------------------------------------------
def run_traceroute(host: str) -> list:
    """
    Run traceroute (Linux) or tracert (Windows).
    Returns a list of hops with ip and latency.
    """
    system = platform.system().lower()
    if system == "windows":
        cmd = ["tracert", "-d", "-h", "20", "-w", "1000", host]
    else:
        # -n  = no DNS reverse lookup (faster)
        # -m  = max hops
        # -w  = wait seconds per probe
        cmd = ["traceroute", "-n", "-m", "20", "-w", "2", host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout

        hops = []
        for line in output.splitlines():
            # Linux format:  " 1  192.168.1.1  1.234 ms  ..."
            # Also handles * * * (timeout hops)
            match = re.match(
                r"^\s*(\d+)\s+(?:\*\s*\*\s*\*|([\d.]+)\s+([\d.]+)\s*ms)",
                line
            )
            if match:
                hop_num = int(match.group(1))
                if match.group(2):
                    ip = match.group(2)
                    latency = float(match.group(3))
                else:
                    ip = "*"
                    latency = 0.0
                hops.append({"hop": hop_num, "ip": ip, "latency": latency})

        return hops if hops else [{"hop": 1, "ip": "timeout", "latency": 0.0}]

    except subprocess.TimeoutExpired:
        return [{"hop": 1, "ip": "timeout", "latency": 0.0}]
    except FileNotFoundError:
        return [{"hop": 1, "ip": "traceroute not available", "latency": 0.0}]
    except Exception:
        return [{"hop": 1, "ip": "error", "latency": 0.0}]


# ---------------------------------------------------------------------------
# DNS Lookup
# ---------------------------------------------------------------------------
def run_dns_lookup(host: str) -> list:
    """
    Query A, AAAA, MX, TXT, NS records using dnspython.
    """
    record_types = ["A", "AAAA", "MX", "TXT", "NS"]
    records = []
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ["8.8.8.8", "1.1.1.1"]  # Google + Cloudflare
    resolver.lifetime = 5.0

    for rtype in record_types:
        try:
            answers = resolver.resolve(host, rtype)
            for rdata in answers:
                if rtype == "MX":
                    value = str(rdata.exchange).rstrip(".")
                    ttl = answers.rrset.ttl
                elif rtype == "TXT":
                    value = " ".join(
                        part.decode("utf-8", errors="replace")
                        for part in rdata.strings
                    )
                    ttl = answers.rrset.ttl
                elif rtype in ("NS",):
                    value = str(rdata.target).rstrip(".")
                    ttl = answers.rrset.ttl
                else:
                    value = str(rdata)
                    ttl = answers.rrset.ttl

                records.append({"type": rtype, "value": value, "ttl": ttl})
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            continue
        except Exception:
            continue

    if not records:
        records.append({"type": "A", "value": "N/A", "ttl": 0})

    return records


# ---------------------------------------------------------------------------
# Port Scan
# ---------------------------------------------------------------------------
def scan_ports(host: str, port_list: list = None) -> list:
    """
    TCP connect scan on each port in port_list.
    Uses a 2-second timeout per port.
    port_list: optional list of {"port": int, "service": str}
    """
    if port_list is None:
        port_list = DEFAULT_PORTS

    results = []
    for entry in port_list:
        port = entry["port"]
        service = entry["service"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            status = "open" if result == 0 else "closed"
        except Exception:
            status = "closed"
        results.append({"port": port, "service": service, "status": status})

    return results


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/diagnose", methods=["POST", "OPTIONS"])
def diagnose():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    body = request.get_json(silent=True)
    if not body or not body.get("target"):
        return jsonify({"error": "target is required"}), 400

    raw_target = body["target"].strip()
    # Strip protocol and path — keep only the hostname
    host = re.sub(r"^https?://", "", raw_target)
    host = re.sub(r"/.*$", "", host)
    host = host.strip()

    if not host:
        return jsonify({"error": "Invalid target"}), 400

    # Optional: caller can pass a custom port list
    # e.g. [{"port": 8080, "service": "HTTP-Alt"}]
    custom_ports = body.get("ports", None)

    ping_result    = run_ping(host)
    traceroute     = run_traceroute(host)
    dns_records    = run_dns_lookup(host)
    port_results   = scan_ports(host, custom_ports)

    return jsonify({
        "ping":       ping_result,
        "traceroute": traceroute,
        "dns":        dns_records,
        "ports":      port_results,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
