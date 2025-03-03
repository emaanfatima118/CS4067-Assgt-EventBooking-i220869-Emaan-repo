from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/payments', methods=['POST'])
def process_payment():
    data = request.json
    user_id = data.get("user_id")
    amount = data.get("amount")
    if not user_id or not amount:
        return jsonify({"error": "Invalid payment data"}), 400

    return jsonify({"message": "Payment successful", "status": "PAID"}), 200

if __name__ == '__main__':
    app.run(port=9000, debug=True)
