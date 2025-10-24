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
To avoid the problem where a high weighting causes interventions from one theme to entire dominate the recommendations, we apply a decay function which reducing a weighting by some $n\%$ when an intervention from that theme is selected.