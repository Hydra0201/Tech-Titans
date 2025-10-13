from flask import Blueprint, jsonify, request
from sqlalchemy import text
from app import get_conn 
from graphviz import Digraph
from flask import Response


graphs_bp = Blueprint("graphs", __name__)

GRAPH_SQL = text("""
    WITH nodes AS (
      SELECT rs.intervention_id, rs.theme_weighted_effectiveness AS score
      FROM runtime_scores rs
      WHERE rs.project_id = :project_id
      ORDER BY rs.theme_weighted_effectiveness DESC
      LIMIT :top_n
    ),
    edges AS (
      SELECT
        ie.cause_intervention    AS src,
        ie.effected_intervention AS dst,
        ie.multiplier,
        CASE
          WHEN ie.multiplier > 1 THEN 1
          WHEN ie.multiplier < 1 THEN -1
          ELSE 0
        END AS sign,
        ABS(ie.multiplier - 1)   AS strength
      FROM intervention_effects ie
      JOIN nodes n1 ON n1.intervention_id = ie.cause_intervention
      JOIN nodes n2 ON n2.intervention_id = ie.effected_intervention
      WHERE ABS(ie.multiplier - 1) >= :epsilon
    )
    SELECT
      (
        SELECT json_agg(json_build_object(
          'id', n.intervention_id,
          'label', COALESCE(i.name, n.intervention_id::text),
          'score', n.score
        ))
        FROM nodes n
        LEFT JOIN interventions i ON i.id = n.intervention_id
      ) AS nodes,
      (
        SELECT json_agg(json_build_object(
          'src', e.src,
          'dst', e.dst,
          'weight', e.sign * e.strength,
          'multiplier', e.multiplier
        ))
        FROM edges e
      ) AS edges;
""")

@graphs_bp.get("/projects/<int:project_id>/graph")
def project_graph(project_id: int):

    try:
        top_n = 30
        epsilon = 0.05
    except ValueError:
        return jsonify({"error": "Invalid top_n or epsilon"}), 400

    with get_conn() as conn:
        row = conn.execute(GRAPH_SQL, {
            "project_id": project_id,
            "top_n": top_n,
            "epsilon": epsilon
        }).mappings().one_or_none()

    if row is None:
        return jsonify({"project_id": project_id, "params": {"top_n": top_n, "epsilon": epsilon}, "nodes": [], "edges": []}), 200

    nodes = row["nodes"] or []
    edges = row["edges"] or []

    return jsonify({
        "project_id": project_id,
        "params": {"top_n": top_n, "epsilon": epsilon},
        "nodes": nodes,
        "edges": edges
    }), 200



def _svg_from_nodes_edges(nodes, edges, title="Intervention Graph"):
    g = Digraph("G", format="svg")
    g.attr(rankdir="LR", labelloc="t", label=title, fontsize="18", fontname="Inter")
    g.attr("graph", bgcolor="white", margin="0.2")

    node_border = "#444444"
    label_gray  = "#555555"
    pos_color   = "#2e7d32"  
    neg_color   = "#c62828"  

    for n in nodes:
        g.node(
            str(n["id"]),
            n.get("label", str(n["id"])),
            shape="box",
            style="rounded,filled",
            fillcolor="white",
            color=node_border,
            fontname="Inter",
            fontcolor=label_gray,
        )

    for e in edges:
        w = float(e["weight"])
        color = pos_color if w >= 0 else neg_color
        penwidth = str(1.0 + min(4.0, abs(w) * 6.0))
        g.edge(
            str(e["src"]), str(e["dst"]),
            color=color,
            penwidth=penwidth,
            arrowsize="0.7",
            label=f'{float(e["multiplier"]):.2f}',
            fontname="Inter",
            fontsize="10",
            fontcolor=label_gray,
        )
    return g.pipe()


@graphs_bp.get("/projects/<int:project_id>/graph.svg")
def project_graph_svg(project_id: int):
    top_n = int(request.args.get("top_n", 30))
    epsilon = 0.05
    with get_conn() as conn:
        row = conn.execute(GRAPH_SQL, {"project_id": project_id, "top_n": top_n, "epsilon": epsilon}).mappings().one_or_none()
    nodes, edges = (row["nodes"] or []), (row["edges"] or [])
    svg_bytes = _svg_from_nodes_edges(nodes, edges, title=f"Project {project_id}")
    return Response(svg_bytes, mimetype="image/svg+xml")