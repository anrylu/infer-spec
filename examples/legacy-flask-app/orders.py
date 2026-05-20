from flask import Blueprint, jsonify, request

bp = Blueprint("orders", __name__)
_ORDERS: dict[int, dict] = {}
_NEXT_ID = 1


@bp.route("", methods=["POST"])
def create_order():
    global _NEXT_ID
    data = request.get_json() or {}
    if "item" not in data:
        return jsonify({"error": "item required"}), 400
    order = {"id": _NEXT_ID, "item": data["item"], "status": "pending"}
    _ORDERS[_NEXT_ID] = order
    _NEXT_ID += 1
    return jsonify(order), 201


@bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id: int):
    o = _ORDERS.get(order_id)
    if o is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(o)
