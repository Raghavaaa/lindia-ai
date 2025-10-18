"""
Job Models and Data Structures
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class JobStatus(str, Enum):
    """Job lifecycle states"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    DEAD_LETTER = "dead_letter"


class Priority(str, Enum):
    """Job priority levels"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    
    def to_int(self) -> int:
        """Convert to numeric priority for sorting (higher = more urgent)"""
        return {"high": 3, "normal": 2, "low": 1}[self.value]


class JobType(str, Enum):
    """Type of AI operation"""
    INFERENCE = "inference"
    EMBEDDING = "embedding"
    SEARCH = "search"


@dataclass
class Job:
    """
    Represents an AI job in the system
    """
    # Core identification
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    idempotency_key: Optional[str] = None
    
    # Job details
    job_type: JobType = JobType.INFERENCE
    payload: Dict[str, Any] = field(default_factory=dict)
    target_provider: Optional[str] = None  # None = use default priority
    
    # Priority and scheduling
    priority: Priority = Priority.NORMAL
    webhook_url: Optional[str] = None
    
    # Lifecycle tracking
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution metadata
    attempt_count: int = 0
    max_attempts: int = 3
    timeout_seconds: int = 60
    provider_timeout_seconds: int = 30
    
    # Results and errors
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider_used: Optional[str] = None
    
    # Tracing
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "idempotency_key": self.idempotency_key,
            "job_type": self.job_type.value,
            "payload": self.payload,
            "target_provider": self.target_provider,
            "priority": self.priority.value,
            "webhook_url": self.webhook_url,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "timeout_seconds": self.timeout_seconds,
            "result": self.result,
            "error": self.error,
            "provider_used": self.provider_used,
            "request_id": self.request_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create Job from dictionary"""
        job = cls(
            job_id=data.get("job_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", ""),
            idempotency_key=data.get("idempotency_key"),
            job_type=JobType(data.get("job_type", "inference")),
            payload=data.get("payload", {}),
            target_provider=data.get("target_provider"),
            priority=Priority(data.get("priority", "normal")),
            webhook_url=data.get("webhook_url"),
            status=JobStatus(data.get("status", "pending")),
            attempt_count=data.get("attempt_count", 0),
            max_attempts=data.get("max_attempts", 3),
            timeout_seconds=data.get("timeout_seconds", 60),
            result=data.get("result"),
            error=data.get("error"),
            provider_used=data.get("provider_used"),
            request_id=data.get("request_id"),
        )
        
        # Parse timestamps
        if data.get("created_at"):
            job.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("queued_at"):
            job.queued_at = datetime.fromisoformat(data["queued_at"])
        if data.get("started_at"):
            job.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            job.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return job


@dataclass
class JobResult:
    """
    Standardized job result
    """
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider_used: Optional[str] = None
    attempt_count: int = 0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "provider_used": self.provider_used,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class BatchRequest:
    """
    Represents a batch of jobs to be processed together
    """
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    jobs: List[Job] = field(default_factory=list)
    provider: str = ""
    job_type: JobType = JobType.INFERENCE
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_job(self, job: Job):
        """Add job to batch"""
        self.jobs.append(job)
    
    def is_compatible(self, job: Job) -> bool:
        """Check if job can be added to this batch"""
        if not self.jobs:
            return True
        return (
            job.job_type == self.job_type and
            (job.target_provider == self.provider or job.target_provider is None)
        )
    
    def size(self) -> int:
        """Get batch size"""
        return len(self.jobs)


@dataclass
class CircuitBreakerState:
    """
    Circuit breaker state for a provider
    """
    provider_name: str
    state: str = "closed"  # closed, open, half_open
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    
    def is_closed(self) -> bool:
        return self.state == "closed"
    
    def is_open(self) -> bool:
        return self.state == "open"
    
    def is_half_open(self) -> bool:
        return self.state == "half_open"

