"""
import grpc
from concurrent import futures
from pymongo import MongoClient
import ledger_pb2
import ledger_pb2_grpc

class LedgerServiceServicer(ledger_pb2_grpc.LedgerServiceServicer):
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27018/")
        self.db = self.client["distributor_ledger"]
        self.col = self.db["transactions"]

    def RecordTransaction(self, request, context):
        data = {
            "batch_id": request.batch_id,
            "sender": request.sender,
            "receiver": request.receiver,
            "status": request.status
        }
        self.col.insert_one(data)
        print(f"🚚 Distributor replicated: {data}")
        return ledger_pb2.TransactionResponse(message="Transaction recorded at Distributor.")

    def GetLedger(self, request, context):
        entries = []
        for tx in self.col.find():
            entries.append(ledger_pb2.LedgerEntry(
                batch_id=tx["batch_id"],
                sender=tx["sender"],
                receiver=tx["receiver"],
                status=tx["status"]
            ))
        return ledger_pb2.LedgerData(entries=entries)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ledger_pb2_grpc.add_LedgerServiceServicer_to_server(LedgerServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("🚚 Distributor node running on port 50052...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
"""

import grpc
from concurrent import futures
from pymongo import MongoClient
import ledger_pb2
import ledger_pb2_grpc
from flask import Flask
import threading

# ---------------------- Health Server ----------------------
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

def start_health_server(port):
    def run():
        app.run(port=port)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# ---------------------- gRPC Service ----------------------
class LedgerServiceServicer(ledger_pb2_grpc.LedgerServiceServicer):
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27018/")
        self.db = self.client["distributor_ledger"]
        self.col = self.db["transactions"]

    def RecordTransaction(self, request, context):
        data = {
            "batch_id": request.batch_id,
            "sender": request.sender,
            "receiver": request.receiver,
            "status": request.status
        }
        self.col.insert_one(data)
        print(f"🚚 Distributor replicated: {data}")
        return ledger_pb2.TransactionResponse(message="Transaction recorded at Distributor.")

    def GetLedger(self, request, context):
        entries = []
        for tx in self.col.find():
            entries.append(ledger_pb2.LedgerEntry(
                batch_id=tx["batch_id"],
                sender=tx["sender"],
                receiver=tx["receiver"],
                status=tx["status"]
            ))
        return ledger_pb2.LedgerData(entries=entries)

# ---------------------- Main Server ----------------------
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ledger_pb2_grpc.add_LedgerServiceServicer_to_server(LedgerServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()

    # Start health endpoint on port 8002 (gRPC 50052 → +3950 = 8002)
    start_health_server(8002)

    print("🚚 Distributor node running on port 50052 with /health on 8002...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
