# carbonbalance/models/__init__.py
"""
Import and register all SQLAlchemy models so Base.metadata knows about them
before you call create_all().  Usage:

    from carbonbalance.models import register_models
    ...
    Base.metadata.create_all(bind=engine)
"""

# Core entities
from .user import User, RoleEnum
from .project import Project
from .theme import Theme
from .project_theme_score import ProjectThemeWeight
from .intervention import Intervention

# Effects and scoring
from .metric_effect import MetricEffect, MetricTypeEnum
from .intervention_effect import InterventionEffect
from .runtime_score import RuntimeScore  # stores adjusted/theme-weighted values

# Recommendations (single-table design with batch id)
from .recommendation import Recommendation

# RBAC per project
from .project_access import ProjectAccess, ProjectRoleEnum


def register_models():
    """
    Return a list of model classes; importing this module is enough for metadata,
    but some apps like to call this explicitly before create_all().
    """
    return [
        User,
        Project,
        Theme,
        ProjectThemeWeight,
        Intervention,
        MetricEffect,
        InterventionEffect,
        RuntimeScore,
        Recommendation,
        ProjectAccess,
    ]


__all__ = [
    # entities
    "User",
    "RoleEnum",
    "Project",
    "Theme",
    "ProjectThemeWeight",
    "Intervention",
    # effects/scoring
    "MetricEffect",
    "MetricTypeEnum",
    "InterventionEffect",
    "RuntimeScore",
    # recommendations
    "Recommendation",
    # rbac
    "ProjectAccess",
    "ProjectRoleEnum",
    # helper
    "register_models",
]
