from flask import Flask, jsonify
from auth import bp as auth_bp
from orders import bp as orders_bp

app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(orders_bp, url_prefix="/orders")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000)
