from flask import Blueprint, request, jsonify
from flask_login import login_required
from services.zakat_service import calculate_zakat

zakat_bp = Blueprint("zakat", __name__)

@zakat_bp.route("/api/calculate-zakat", methods=["POST"])
@login_required
def calculate():
    data = request.get_json()
    result = calculate_zakat(data)
    return jsonify(result.__dict__)
