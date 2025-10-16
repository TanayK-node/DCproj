import grpc
import ledger_pb2
import ledger_pb2_grpc

def record_transaction(batch_id, sender, receiver, status):
    with grpc.insecure_channel('localhost:50051') as channel:  # Only talk to Factory
        stub = ledger_pb2_grpc.LedgerServiceStub(channel)
        response = stub.RecordTransaction(ledger_pb2.TransactionRequest(
            batch_id=batch_id,
            sender=sender,
            receiver=receiver,
            status=status
        ))
        print(response.message)

if __name__ == "__main__":
    record_transaction("MED1001", "Factory", "Distributor", "Shipped")
    record_transaction("MED1001", "Distributor", "Pharmacy", "Delivered")
    record_transaction("MED1001", "Pharmacy", "Patient", "Sold")
