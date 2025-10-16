"""
import grpc
import ledger_pb2
import ledger_pb2_grpc
from itertools import cycle
from flask import Flask, request, jsonify

# List of backend nodes (you can add more)
NODES = ["localhost:50051", "localhost:50052", "localhost:50053"]

# Create a round-robin iterator
node_cycle = cycle(NODES)

app = Flask(__name__)

@app.route("/record", methods=["POST"])
def record_transaction():
    data = request.json
    # Pick next node
    node = next(node_cycle)
    print(f"📦 Routing request to {node}")

    try:
        with grpc.insecure_channel(node) as channel:
            stub = ledger_pb2_grpc.LedgerServiceStub(channel)
            response = stub.RecordTransaction(
                ledger_pb2.TransactionRequest(
                    batch_id=data["batch_id"],
                    sender=data["sender"],
                    receiver=data["receiver"],
                    status=data["status"],
                )
            )
        return jsonify({"message": response.message, "node_used": node})
    except Exception as e:
        return jsonify({"error": str(e), "node_used": node}), 500

@app.route("/")
def home():
    return "Load Balancer is running 🚀"

if __name__ == "__main__":
    app.run(port=8080)
"""
import grpc
import ledger_pb2
import ledger_pb2_grpc
from flask import Flask, request, jsonify
import os
import requests
import threading
import time

# Health ports corresponding to gRPC ports
HEALTH_PORTS = {
    "localhost:50051": 8001,  # Factory
    "localhost:50052": 8002,  # Distributor
    "localhost:50053": 8003   # Pharmacy
}

# Path to file where monitor writes the active primary
PRIMARY_FILE = "active_primary.txt"

# Flask app
app = Flask(__name__)

def get_active_primary():
    """Read the currently active primary from the file"""
    if os.path.exists(PRIMARY_FILE):
        with open(PRIMARY_FILE, "r") as f:
            port = f.read().strip()
            return f"localhost:{port}"
    # Default primary if file missing
    return "localhost:50051"

def is_alive(node):
    """Check node health by pinging its /health endpoint"""
    health_port = HEALTH_PORTS.get(node)
    if not health_port:
        return False
    try:
        res = requests.get(f"http://{node.split(':')[0]}:{health_port}/health", timeout=2)
        return res.status_code == 200
    except Exception:
        return False

@app.route("/record", methods=["POST"])
def record_transaction():
    data = request.json
    node = get_active_primary()

    # Validate node health before routing
    if not is_alive(node):
        return jsonify({
            "error": f"Primary {node} is down. Please wait for failover.",
            "node_used": node
        }), 503

    print(f"📦 Routing request to active primary: {node}")

    try:
        with grpc.insecure_channel(node) as channel:
            stub = ledger_pb2_grpc.LedgerServiceStub(channel)
            response = stub.RecordTransaction(
                ledger_pb2.TransactionRequest(
                    batch_id=data["batch_id"],
                    sender=data["sender"],
                    receiver=data["receiver"],
                    status=data["status"],
                )
            )
        return jsonify({"message": response.message, "node_used": node})
    except Exception as e:
        return jsonify({"error": str(e), "node_used": node}), 500

@app.route("/")
def home():
    primary = get_active_primary()
    return f"Load Balancer is running 🚀<br>Current Primary: {primary}"

# ---------------------- Optional: Background health monitor ----------------------
def background_health_check():
    """Periodically logs which node is active and healthy"""
    while True:
        primary = get_active_primary()
        status = "✅" if is_alive(primary) else "❌"
        print(f"[Monitor] Primary: {primary} {status}")
        time.sleep(5)

if __name__ == "__main__":
    # Run background thread to show health info
    threading.Thread(target=background_health_check, daemon=True).start()
    app.run(port=8080)
