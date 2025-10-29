# Scoring Heuristic

CarbonBalance uses a combination of heuristic rules to produce scores which determine the ranking of interventions.

The origin point of the scoring logic is [base effectiveness](../architecture/philosophy.md#base-effectiveness), a term which describes a base numerical score given to an intervention. A base effectiveness score is assigned to each intervention in the "interventions" database table. These values are not modified during runtime, and are global for all users.

## Building Metrics

When a user creates a new project in order to receieve intervention recommendations, they are first prompted to enter a collection of [building metrics](../architecture/philosophy.md#building-metrics). These metrics will then be checked against rules in the `metric_effects` table.

### Example

| id  | cause                           | effected_intervention            | lower_bound | upper_bound | multiplier |
|-----|---------------------------------|----------------------------------|-------------|-------------|------------|
| 1   | Basement Area : GIFA            | Remove basement                  | 0.50        | NULL        | 1.5        |
| 2   | Basement Area : GIFA            | Remove basement                  | 0.31        | 0.49        | 1.3        |
| 3   | Basement Area : GIFA            | Remove basement                  | 0.30        | 0.16        | 1.1        |
| 4   | Basement Area : GIFA            | Remove basement                  | 0.00        | 0.04        | 0.5        |
| 5   | Basement Area : GIFA            | Remove basement                  | 0.05        | 0.09        | 0.7        |
| 6   | Basement Area : GIFA            | Remove basement                  | 0.10        | 0.15        | 0.9        |

### Effect Table

The rule row with id 1 states that if a Basement Area : GIFA ratio is >= 0.5, the "Remove basement" intervention's base effectiveness will be multiplied by 1.5 to determine its runtime score. Each of these multiplier values corresponds to the scheme set out in the following table:
<table>
  <tr>
    <th></th><th>Positive</th><th>Negative</th>
  </tr>
  <tr>
    <th>Strong</th><td>1.5</td><td>0.5</td>
  </tr>
  <tr>
    <th>Moderate</th><td>1.3</td><td>0.7</td>
  </tr>
  <tr>
    <th>Weak</th><td>1.1</td><td>0.9</td>
  </tr>
</table>

So if the Basement Area : GIFA ratio is between 0.10 and 0.15, this will have a Weak Negative effect on the base effectiveness of "Remove basement".


## Weighting

Weighting is a scaling factor which is intended to reflect the user's relative preferences for specific [themes](../architecture/philosophy.md#themes). The higher weighting given to a theme, the more likely they user is to be offered interventions from that theme.

**Normalisation:**
We can capture proportional intent by placing the weightings in the context of all other weighting decisions. Weighting becomes **relational** rather than **absolute**.
E.g.:
$\text{Reducing Embodied Carbon} = 5$

$\text{Reducing Operational Carbon} = 3$

$\text{Renewable Energy Supply} = 4$

$\text{Total = 5+3+4 = 12}$

$\text{Reducing Embodied Carbon} = \frac{5}{total} = \frac{5}{12} = 0.41$
$\text{Reducing Operational Carbon} = \frac{3}{total} = \frac{3}{12} = 0.25$
$\text{Renewable Energy Supply} = \frac{4}{total} = \frac{4}{12} = 0.33$

Now we apply these weighting multipliers to each of the interventions contained in these themes. E.g., every intervention in "Reducing Operational Carbon" will be multiplied by $0.25$.

**Diminishing returns:**
If a user assigns a high weighting to a single theme (e.g. Reducing Embodied Carbon = 0.7), that theme would otherwise dominate the recommendation rankings. To prevent the system from repeatedly suggesting interventions from only one theme, diminishing returns are used.

Each time the user selects an intervention from a theme, that theme’s influence is temporarily reduced by applying a decay function to its weighting. This simulates preference satisfaction: after choosing one intervention from a theme, it becomes slightly less urgent to see more suggestions from that same theme immediately.

The decay is multiplicative:

$$w_\text{new} = max(floor, w_\text{raw} \times \alpha)$$

Where:
- $w_\text{raw}$ is the unnormalise theme weight
- $\alpha$ is a retention factor ($0 \leq \alpha \leq 1)
  - E.g., $\alpha = 0.6$ keeps 60% of the weight after a selection
- `floor` ensures no theme ever fully disappears from consideration.

After decaying the theme weight, all themes are **renormalised** so that they still represent a probability-like distribution summing to 1.

### Example

| Theme                       | Raw Weight (Before) | Raw Weight (After 1 Selection, α=0.6) |
| --------------------------- | ------------------- | ------------------------------------- |
| Reducing Embodied Carbon    | 5                   | 3 *($\rightarrow$ decayed)*           |
| Reducing Operational Carbon | 3                   | 3                                     |
| Renewable Energy Supply     | 2                   | 2                                     |

In this selection, the relative influence of *Reducing Embodied Carbon* is reduced, which encourages variety and balance in further recommendations.

## Intervention Dependency Effects

Interventions are not entirely isolate phenomenon; by this I mean, the implementation of intervention $x$ might *reduce* or *improve* the effectiveness of intervention $y$. To model this behaviour, CarbonBalance consults an additional rules table, `InterventionEffects`.

### Example scenario

| Cause Intervention                     | Effected Intervention                                           |
| -------------------------------------- | --------------------------------------------------------------- |
| External Wall U-Value Enhancements | Optimised External Shading – Physical Solar Shading (Fixed) |

Both of these interventions reduce unwanted heat transfer through the building envelope. Wall insulation improves thermal resistance, while external shading reduces solar heat gain. However, once insulation has already been improved, the additional benefit from shading is reduced because some of the thermal performance gain has already been achieved.

| id | cause_intervention | effected_intervention | metric_type | lower_bound | upper_bound | multiplier |
| -- | ------------------ | --------------------- | ----------- | ----------- | ----------- | ---------- |
| 1  | 12                 | 16                    | ratio       | 0.80        | 1.30        | 0.7        |

This rule states:
> If **External Wall U-Value Enhancements** have been applied, then **Optimised External Shading** becomes 30% less effective (multiplier 0.7). This is a [Moderate Negative](../architecture/scoring.md#effect-table), modelling diminishing returns from overlapping thermal strategies.



