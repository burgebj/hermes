"""Bundled Dense Associative Memory package for Hermes LCM.

Provides the core DAM components as a first-party package under agent.lcm.dam,
eliminating the need for sys.path hacks in tests and enabling clean imports.
"""
from plugins.context_engine.lcm.dam.network import DenseAssociativeMemory
from plugins.context_engine.lcm.dam.encoder import MessageEncoder
from plugins.context_engine.lcm.dam.retrieval import DAMRetriever
from plugins.context_engine.lcm.dam.persistence import save_state, load_state

__all__ = [
    "DenseAssociativeMemory",
    "MessageEncoder",
    "DAMRetriever",
    "save_state",
    "load_state",
]
