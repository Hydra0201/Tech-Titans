from flask import Blueprint, request, jsonify

scaling_bp = Blueprint('scaling', __name__)

@scaling_bp.route('/dependencies/<int:intervention_id>', methods=['GET'])
def get_dependencies(intervention_id): 
    # This route gives all the dependency effects for implementing a specific intervention
    print(f"Fetching dependencies for implementing intervention with intervention ID: {intervention_id}")
    # Pull project BM from DB
    dummy_data = {"affected_intervention": "External Wall U-Value enhancements", "effect_strength": "moderate"}
    return jsonify({"dependencies": dummy_data}), 200

@scaling_bp.route('/dependencies/<int:intervention_id>/reasoning', methods=['GET'])
def get_dependency_reasoning(intervention_id):
    # This is a helper route to pull the reasoning for an dependency from the DB
    dummy_reasoning = {"reasoning": "Moderate basement proportion, removing it likely has a noticeable impact."}
    return jsonify({"reasoning": dummy_reasoning}), 200

@scaling_bp.route('/metric_dependencies/<int:project_id>', methods=['GET'])
def get_metric_dependencies(project_id):
    # This routes gives all the dependency effects resulting from the project's building metrics
    # This will get called AFTER the send_metrics route in building_metrics.py

    # The logic here will pull the building metrics for the given project_id, check the scaling rules to determine the effect strength,
    # and return the affected interventions and the strength of the effect (weak/moderate/strong) and whether it is a positive or negative effect (polarity)
    dummy_data =  [       
        {
            "affected_intervention": "Low waste design strategy",
            "effect_strength": "moderate",
            "polarity": "positive"
        },
        {
            "affected_intervention": "Utilising exposed soffits",
            "effect_strength": "strong",
            "polarity": "negative"
        },
        {
            "affected_intervention": "Retention of existing structures",
            "effect_strength": "weak",
            "polarity": "positive"
        }
    ]

    return jsonify({"metric_dependencies": dummy_data}), 200
