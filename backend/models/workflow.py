"""
Workflow state models.
"""

from dataclasses import dataclass
from typing import Literal, Any
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = 'pending'
    SCANNING_MARKET = 'scanning_market'
    DETECTING_SURPLUS = 'detecting_surplus'
    NEGOTIATING = 'negotiating'
    AWAITING_CONFIRMATION = 'awaiting_confirmation'
    COMPLETED = 'completed'
    FAILED = 'failed'


@dataclass
class WorkflowState:
    """
    Complete state of a workflow execution.
    """
    workflow_id: str
    status: WorkflowStatus
    farmer_input: dict
    market_scan: dict | None
    surplus_analysis: dict | None
    negotiation_messages: list[dict]
    negotiation_result: dict | None
    blended_income: float | None
    created_at: str
    updated_at: str
    error: str | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DynamoDB."""
        return {
            'workflow_id': self.workflow_id,
            'status': self.status.value if isinstance(self.status, WorkflowStatus) else self.status,
            'farmer_input': self.farmer_input,
            'market_scan': self.market_scan,
            'surplus_analysis': self.surplus_analysis,
            'negotiation_messages': self.negotiation_messages,
            'negotiation_result': self.negotiation_result,
            'blended_income': self.blended_income,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'error': self.error,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WorkflowState':
        """Create from dictionary."""
        return cls(
            workflow_id=data['workflow_id'],
            status=WorkflowStatus(data['status']),
            farmer_input=data['farmer_input'],
            market_scan=data.get('market_scan'),
            surplus_analysis=data.get('surplus_analysis'),
            negotiation_messages=data.get('negotiation_messages', []),
            negotiation_result=data.get('negotiation_result'),
            blended_income=float(data['blended_income']) if data.get('blended_income') else None,
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            error=data.get('error'),
        )
