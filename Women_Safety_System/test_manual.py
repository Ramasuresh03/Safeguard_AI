import requests

data = {
 "heart_rate":135,
 "bp":"165/105",
 "spo2":89,
 "stress":"High"
}

requests.post("http://127.0.0.1:5000/receive-data", json=data)
print("Sent")
