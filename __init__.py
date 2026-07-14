"""Apertis AI directory-plugin entry point for Hermes Agent."""

from .hermes_apertis_provider import apertis, register


register()

__all__ = ("apertis", "register")
