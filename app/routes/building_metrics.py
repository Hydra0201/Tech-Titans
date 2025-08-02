from flask import Blueprint, request, jsonify

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/send_metrics', methods=['POST'])
def send_metrics():
    data = request.get_json()
    # Route to POST project building metrics to DB
    # The JSON payload will include the building metrics and the project name

    if not data: # Should also check that building metrics and project name are in data as expected
        return jsonify({"message": "Error: Form data does not match expected format."}), 400 
    
    # DB Update logic here
    return jsonify({"message": "Successfully send building metrics to DB"}), 201

@metrics_bp.route('/get_metrics/<int:project_id>', methods=['GET'])
def get_metrics(project_id):
    print(f"Fetching building metrics for project ID: {project_id}")
    # Pull project BM from DB
    return jsonify({"message": "Successfully retrieved building metrics from DB"}), 200