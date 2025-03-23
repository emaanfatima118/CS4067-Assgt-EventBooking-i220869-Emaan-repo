from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/payments', methods=['POST'])
def process_payment():
    data = request.json
    try:
        user_id = int(data.get("user_id"))
        amount = float(data.get("amount"))

        if user_id <= 0 or amount <= 0:
            return jsonify({"error": "Invalid payment data"}), 400

        return jsonify({"message": "Payment successful", "status": "PAID"}), 200

    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input type"}), 400

if __name__ == '__main__':
    app.run(port=9000, debug=True)
