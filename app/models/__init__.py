# carbonbalance/models/__init__.py

# Core entities
from .user import User, RoleEnum, AccessLevelEnum
from .project import Project
from .theme import Theme
from .project_theme_weightings import ProjectThemeWeighting  
from .intervention import Intervention

# Effects and scoring
from .metric_effect import MetricEffect, MetricTypeEnum
from .intervention_effect import InterventionEffect
from .runtime_score import RuntimeScore

# Recommendations (snapshot table)
from .recommendation import Recommendation

# RBAC per project
from .project_access import ProjectAccess

# NEW — stages, implemented, app config
from .stages import Stage
from .implemented_intervention import ImplementedIntervention
from .app_config import Config as AppConfig


def register_models():
    return [
        User,
        Project,
        Theme,
        ProjectThemeWeighting,
        Intervention,
        MetricEffect,
        InterventionEffect,
        RuntimeScore,
        Recommendation,
        ProjectAccess,
        Stage,
        ImplementedIntervention,
        AppConfig,
    ]

__all__ = [
    "User", "RoleEnum", "AccessLevelEnum",
    "Project",
    "Theme",
    "ProjectThemeWeighting",
    "Intervention",
    "MetricEffect", "MetricTypeEnum",
    "InterventionEffect",
    "RuntimeScore",
    "Recommendation",
    "ProjectAccess",
    "Stage",
    "ImplementedIntervention",
    "AppConfig",
    "register_models",
]
