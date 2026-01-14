"""
Admin module for enterprise CX agent.

Contains administrative features like decision trace viewing,
user management, and audit log analysis.
"""

from admin.decision_reviewer import handle_admin_query

__all__ = ['handle_admin_query']
