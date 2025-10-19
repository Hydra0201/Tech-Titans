from sqlalchemy import text, TextClause

interventions = text("""
INSERT INTO interventions (name, theme_id, base_effectiveness, is_stage)
VALUES (:name, :theme_id, :base_effectiveness, :is_stage)
ON CONFLICT (name) DO UPDATE
  SET theme_id = EXCLUDED.theme_id,
      base_effectiveness = EXCLUDED.base_effectiveness,
      is_stage = EXCLUDED.is_stage
""")


themes: TextClause = text("""
    INSERT INTO themes (id, name)
    VALUES (:id, :name)
    ON CONFLICT (id) DO UPDATE
    SET name = EXCLUDED.name
""")



metric_effects: TextClause = text("""
  INSERT INTO metric_effects
    (cause, effected_intervention, metric_type, lower_bound, upper_bound, multiplier)
  VALUES
    (:cause, :effected_intervention, :metric_type, :lower_bound, :upper_bound, :multiplier)
""")

intervention_effects: TextClause = text("""
  INSERT INTO intervention_effects
    (cause_intervention, effected_intervention, metric_type, lower_bound, upper_bound, multiplier)
  VALUES
    (:cause_intervention, :effected_intervention, :metric_type, :lower_bound, :upper_bound, :multiplier)
""")


stages = text("""
  INSERT INTO stages (src_intervention_id, dst_intervention_id, relation_type)
  VALUES (:src_intervention_id, :dst_intervention_id, :relation_type)
  ON CONFLICT ON CONSTRAINT stages_pkey DO NOTHING
""")