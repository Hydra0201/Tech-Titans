from flask import Blueprint, request, jsonify

interventions_bp = Blueprint('interventions', __name__)

@interventions_bp.route('/get_intervention/<int:intervention_id>', methods=['GET'])
def get_intervention(intervention_id):
    print(f"Fetching base effectiveness and theme for intervention id: {intervention_id}")
    # Pull BE and theme from DB
    return jsonify({"id": 1, "name": "Add External Shading", "theme": "Reducing Operational Carbon", "base_effectiveness": 5}), 200

@interventions_bp.route('get_all_interventions', methods=['GET'])
def get_all_interventions():
    print(f"Retrieving base effectiveness, theme, name, and ID for all interventions")

    # TODO: Replace with DB query fetching all interventions
    dummy_interventions = [
        {
            "id": 1,
            "name": "Install Solar Panels",
            "theme": "Reducing Operational Carbon",
            "base_effectiveness": 4
        },
        {
            "id": 2,
            "name": "Upgrade HVAC System",
            "theme": "Water Efficiency",
            "base_effectiveness": 6
        },
        {
            "id": 3,
            "name": "Add External Shading",
            "theme": "Reducing Operational Carbon",
            "base_effectiveness": 5
        }
    ]
    return jsonify({"interventions": dummy_interventions}), 200