import grpc
from concurrent import futures
from pymongo import MongoClient
import ledger_pb2
import ledger_pb2_grpc
import threading, time

REPLICA_PORTS = [50052, 50053]   # distributor + pharmacy

class LedgerServiceServicer(ledger_pb2_grpc.LedgerServiceServicer):
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["factory_ledger"]
        self.col = self.db["transactions"]

    # ----------- replication function -----------
    def propagate_to_replicas(self, data):
        for port in REPLICA_PORTS:
            try:
                with grpc.insecure_channel(f"localhost:{port}") as channel:
                    stub = ledger_pb2_grpc.LedgerServiceStub(channel)
                    stub.RecordTransaction(ledger_pb2.TransactionRequest(
                        batch_id=data["batch_id"],
                        sender=data["sender"],
                        receiver=data["receiver"],
                        status=data["status"]
                    ))
                print(f"✅ Replicated to replica on port {port}")
            except Exception as e:
                print(f"⚠️ Failed to replicate to port {port}: {e}")

    # ----------- gRPC endpoint -----------
    def RecordTransaction(self, request, context):
        data = {
            "batch_id": request.batch_id,
            "sender": request.sender,
            "receiver": request.receiver,
            "status": request.status
        }
        self.col.insert_one(data)
        print(f"🏭 Factory recorded: {data}")

        # --- Choose one consistency model ---

        # STRONG CONSISTENCY  → wait for replicas before responding
        # self.propagate_to_replicas(data)
        # return ledger_pb2.TransactionResponse(message="Recorded & replicated (Strong Consistency).")

        # EVENTUAL CONSISTENCY → replicate asynchronously
        threading.Thread(target=self.propagate_to_replicas, args=(data,)).start()
        return ledger_pb2.TransactionResponse(message="Recorded at Factory (Eventual Consistency).")

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
    server.add_insecure_port("[::]:50051")
    server.start()
    print("🏭 Factory node running on port 50051...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
