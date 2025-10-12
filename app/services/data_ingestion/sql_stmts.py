from sqlalchemy import text, TextClause

interventions: TextClause = text("""
    INSERT INTO interventions (id, name, theme_id, base_effectiveness)
    VALUES (:id, :name, :theme_id, :base_effectiveness)
    ON CONFLICT (id) DO UPDATE
    SET name = EXCLUDED.name,
        theme_id = EXCLUDED.theme_id,
        base_effectiveness = EXCLUDED.base_effectiveness
""")


themes: TextClause = text("""
    INSERT INTO themes (id, name)
    VALUES (:id, :name)
    ON CONFLICT (id) DO UPDATE
    SET name = EXCLUDED.name
""")



metric_effects: TextClause = text("""
  INSERT INTO metric_effects
    (id, cause, effected_intervention, metric_type, lower_bound, upper_bound, multiplier)
  VALUES
    (:id, :cause, :effected_intervention, :metric_type, :lower_bound, :upper_bound, :multiplier)
  ON CONFLICT (id) DO UPDATE
  SET cause = EXCLUDED.cause,
      effected_intervention = EXCLUDED.effected_intervention,
      metric_type = EXCLUDED.metric_type,
      lower_bound = EXCLUDED.lower_bound,
      upper_bound = EXCLUDED.upper_bound,
      multiplier = EXCLUDED.multiplier
""")


intervention_effects: TextClause = text("""
  INSERT INTO intervention_effects
    (id, cause_intervention, effected_intervention, metric_type, lower_bound, upper_bound, multiplier)
  VALUES
    (:id, :cause_intervention, :effected_intervention, :metric_type, :lower_bound, :upper_bound, :multiplier)
  ON CONFLICT (id) DO UPDATE
  SET cause_intervention = EXCLUDED.cause_intervention,
      effected_intervention = EXCLUDED.effected_intervention,
      metric_type = EXCLUDED.metric_type,
      lower_bound = EXCLUDED.lower_bound,
      upper_bound = EXCLUDED.upper_bound,
      multiplier = EXCLUDED.multiplier
""")

stages: TextClause = text("""
  INSERT INTO stages (src_intervention_id, dst_intervention_id, relation_type)
  VALUES (:src_intervention_id, :dst_intervention_id, :relation_type)
  ON CONFLICT ON CONSTRAINT stages_pkey DO NOTHING
""")