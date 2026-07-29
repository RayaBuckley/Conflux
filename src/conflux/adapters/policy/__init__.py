"""External policy adapters; none is an authority source without injection."""

from .aws import AWSSubsetDecision, evaluate_statement

__all__ = ["AWSSubsetDecision", "evaluate_statement"]
