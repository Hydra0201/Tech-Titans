# System Design Philosophy

This document is written for future developers, maintainers, and stakeholders to understand the system's intent before engaging with technical/architectural details.

## Purpose
CarbonBalance is a tool to support sustainability decision-making in early-stage construction projects where data is uncertain and expert judgment still dominates. Instead of trying to provide exact answers, the system organises expert knowledge into a transparent heuristic model that can rank sustainability interventions, explore trade-offs, and communicate reasoning.

### System Assumptions

1. Core data (interventions, themes, rules) is maintained by an administrative user with domain expertise.
2. Early-stage sustainability evaluation benefits more from **ranked guidance** than exact numerical predictions.
3. Each intervention can be assigned a baseline impact (**base effectiveness**) independent of specific project context.
4. Cost guidance is abstracted as **cost tokens**, representing feasibility rather than literal cost values.

### Design Principles
- Scoring should be deterministic, i.e. a given set of inputs should always produce the same output.
- **Interactivity** - the system makes suggests, but the user is allowed to decide.
    - Maintaining some level of choice gives the user an impression of both control and responsibility
- **Extendability** - future rules and data should be easy to evolve (i.e., don't hardcode them, represent them in a modifiable form)

## Problem Context
Early in the project, I had hoped to build a system based on hard data which would take some project parameters as input and output a list of ideal interventions. Unfortunately, this was simply not possible; during the early planning stage of a construction project there is a great deal of uncertainty, and overly general suggestions are much more valuable than accurate, specific recommendations, as any extant project data is subject to change, and decisions are tentative. In my view, a heuristic system is the only reasonable way to approach the problem of sustainable intervention recommendation for early-stage construction projects.

## Core Ideas
CarbonBalance implements a heuristic model intended to reflect Costplan's proprietary knowledge of sustainable construction interventions, a major challenge and goal in designing this system has been to create a simple means by which this knowledge can be translated to a combination of numeric values and logical rules in a general fashion.

I go into deeper detail discussion implementation in successive sections, but I'll begin by describing the key ideas driving this heuristic model.

### Pre-existing
These are concepts which have been directly taken from Costplan rather than invented to fit the heuristic system.

#### Interventions

An intervention is an action which can be taken to improve sustainability in a construction project. For example, "Enhanced Construction Monitoring" can reduce *embodied carbon* by ensuring material waste is low, while "Glazing Ratio Improvement" (i.e., choosing an appropriate window-to-wall ratio for the building and climate) reduces unwanted heat losses and solar gains while preserving useful daylight, which lowers HVAC and lighting energy use and thus *operational carbon*.

!!! note "Sustainability Themes" 
    *Operational carbon* and *embodied carbon* are examples of **themes**

#### Themes
Sustainability is multifaceted in that it is not a singular aim that interventions each contribute some flat amount of value to. Instead, sustainability can be broken up into themes which each may be more or less appropriate/achievable for a given construction project. These themes can be found in the 'Matrix' tab of the "P2035 - Sustainability Cost Matrix" document, and each intervention has been sorted into a theme in the "Detailed Matrix" tab, but you must first Unfreeze Panes (View -> Freeze Panes -> Unfreeze Panes) for them to be visible.

### Heuristic concepts
These are concepts which were created to facilitate the heuristic model developed to run CarbonBalance

#### Base effectiveness
The most basic assumption underpinning this model is that each intervention can be given a baseline effectiveness value which represents the inherent difference between interventions. Not all interventions are born equal, i.e. "Wayfinding Signage" will have a negligible impact on sustainability, while "Remove basement" will tend to have a fairly significant effect, as basement typically require a great deal of reinforced concrete, which has a high carbon footprint; removing this can greatly decrease $CO_2$. 

This "base effectiveness" value is used as the baseline for every project, and is scaled by:

1. Building metrics
    - This is used to represent difference between projects.
    - E.g.:
        - External wall area
        - GIFA
        - Levels
        - ...
2. Theme weightings
    - Users set weightings to represent how much they care about specific themes
3. Intervention dependencies
    - Complex dependencies often exist between interventions, e.g. if "Implementation of physical security measures" is implemented, "Security Risk Assessment" will have less overall impact, as there is a smaller capacity for improvement (i.e., overlapping interventions can be wasteful).

## User Experience
A simplified version of the ideal user experience can be modelled in the following way:

1. The user inputs their project metrics, or chooses a preset which is reasonably close to their project expectations
2. A selection of sliders for each theme is presented to the user. These can be set to represent how much the user cares about each theme
3. The $n$ best interventions are displayed to the user, they may pick one
4. After an intervention is selected, cost tokens are displayed representing, in an abstract way, the cost of the selected interventions.
5. The user will continue selecting an intervention from the pool in a loop. After each selection, scores are recalculated and a new set of interventions are recommended accordingly.
6. Once the user decides they have chosen enough interventions or the cost rating has grown too high, they may choose to end the recommendation process.
7. The list of implemented interventions and a graph displaying the relationships between selected interventions is displayed to the user.

## Scoring Model
As alluded to, the scoring model involves starting off by giving each intervention a score, then scaling these score in accordance with:
- Building metrics
- Theme weightings
- Dependencies between interventions

In our model, we consider the "best" intervention to be whichever has the highest score after all relevant scaling is applied.

Further detail about the specifics of the scoring model and its usage is provided in the "Scoring" page.
