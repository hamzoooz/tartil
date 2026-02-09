"""
Template tags for messages
"""
from django import template

register = template.Library()


@register.filter
def is_read_by(message, user):
    """Check if a message is read by a user"""
    return message.is_read_by(user)
