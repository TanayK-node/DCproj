import time
import requests

# Primary–Backup configuration
NODES = [
    {"name": "Factory", "grpc_port": 50051, "health_port": 8001},
    {"name": "Distributor", "grpc_port": 50052, "health_port": 8002},
    {"name": "Pharmacy", "grpc_port": 50053, "health_port": 8003},
]

PRIMARY_FILE = "active_primary.txt"
HEARTBEAT_INTERVAL = 3  # seconds
FAIL_THRESHOLD = 3      # consecutive failures before failover

def is_alive(health_port):
    """Check if node's health endpoint responds"""
    try:
        res = requests.get(f"http://localhost:{health_port}/health", timeout=2)
        return res.status_code == 200
    except Exception:
        return False

def write_primary(port):
    """Write current primary gRPC port to file"""
    with open(PRIMARY_FILE, "w") as f:
        f.write(str(port))
    print(f"🔁 Active primary updated → {port}")

def monitor_nodes():
    current_primary_index = 0
    fail_count = 0

    print(f"🚀 Monitoring started. Primary: {NODES[current_primary_index]['name']} ({NODES[current_primary_index]['grpc_port']})")
    write_primary(NODES[current_primary_index]["grpc_port"])

    while True:
        primary = NODES[current_primary_index]
        alive = is_alive(primary["health_port"])

        if alive:
            print(f"✅ {primary['name']} healthy")
            fail_count = 0
        else:
            fail_count += 1
            print(f"❌ Heartbeat failed ({fail_count}/{FAIL_THRESHOLD}) for {primary['name']}")
            if fail_count >= FAIL_THRESHOLD:
                # Promote next available backup
                next_index = (current_primary_index + 1) % len(NODES)
                new_primary = NODES[next_index]
                print(f"⚠️ Promoting {new_primary['name']} as new Primary")
                write_primary(new_primary["grpc_port"])
                current_primary_index = next_index
                fail_count = 0
                time.sleep(3)  # small delay for system to stabilize

        time.sleep(HEARTBEAT_INTERVAL)

if __name__ == "__main__":
    monitor_nodes()
