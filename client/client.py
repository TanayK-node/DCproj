import requests

def record_transaction(batch_id, sender, receiver, status):
    # Prepare the transaction data
    payload = {
        "batch_id": batch_id,
        "sender": sender,
        "receiver": receiver,
        "status": status
    }

    # Send to Load Balancer API instead of direct gRPC
    try:
        response = requests.post("http://localhost:8080/record", json=payload)
        if response.status_code == 200:
            print(f"✅ {response.json()}")
        else:
            print(f"⚠️ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error connecting to Load Balancer: {e}")

if __name__ == "__main__":
    record_transaction("MED1001", "Factory", "Distributor", "Shipped")
    record_transaction("MED1001", "Distributor", "Pharmacy", "Delivered")
    record_transaction("MED1001", "Pharmacy", "Patient", "Sold")
