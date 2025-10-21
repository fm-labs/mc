import time

# from random import randint
#
# from scapy.layers.inet import IP, ICMP
# from scapy.sendrecv import sr1

from mc.db.mongodb import get_mongo_collection
from mc.inventory.item.host import handle_host_ping

# def ping(dst: str):
#     pkt = IP(dst=dst) / ICMP(id=randint(0, 0xFFFF), seq=1) / b"hello"
#     reply = sr1(pkt, timeout=2, verbose=False)
#
#     if reply:
#         rtt_ms = (reply.time - pkt.time) * 1000.0
#         print(f"Reply from {reply.src}: icmp_seq=1 time={rtt_ms:.2f} ms")
#         return rtt_ms
#     else:
#         print("Request timed out")
#     return None


if __name__ == "__main__":

    host_collection = get_mongo_collection("inventory", "host")
    findings_collection = get_mongo_collection("findings", "findings")

    filters = {"properties.monitoring_enabled": True}
    hosts = host_collection.find(filters)
    for host in hosts:
        print(host)
        ping_result = handle_host_ping(host, {})
        # props = host.get("properties", {})
        # hostname = props.get("hostname")
        # if not hostname:
        #    print("Skipping host with no hostname")
        #    continue

        # ping_result = ping(hostname)
        print("PING RESULT:", ping_result)
        if ping_result is None:
            print("PING RESULT IS EMPTY. HOST MAY NOT BE REACHABLE.")

        # update host document
        host_collection.update_one({"_id": host.get("_id")},
                                   {"$set": {"ping": {
                                       "result": ping_result,
                                       "timestamp": int(time.time())
                                   }}})

        # create or update finding
        severity = 0 # "info"
        message = "Host reachable"

        if ping_result is None or ping_result.get("status") != "reachable":
            #severity = "warning"
            severity = 3
            message = "Host not reachable"

        finding = {
            "resource_type": "host",
            "resource_id": str(host.get("_id")),
            "resource_name": host.get("name", str(host.get("_id"))),
            "check_name": "ping",
            "details": ping_result,
            "severity": severity,
            "timestamp": int(time.time()),
            "message": message
        }
        findings_collection.update_one({
            "resource_type": "host",
            "resource_id": str(host.get("_id")),
            "type": "ping"},
            {
                "$set": finding,
                "$setOnInsert": {"first_seen": int(time.time())}
            }, upsert=True)
