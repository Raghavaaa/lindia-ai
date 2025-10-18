"""
Vector Store Data Models
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import numpy as np


class OperationType(str, Enum):
    """Type of vector operation"""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    REBUILD = "rebuild"
    SNAPSHOT = "snapshot"


class IndexType(str, Enum):
    """FAISS index types"""
    FLAT = "Flat"  # Exact search, no compression
    IVF_FLAT = "IVFFlat"  # Inverted file with flat storage
    IVF_PQ = "IVFPQ"  # Inverted file with product quantization
    HNSW = "HNSW"  # Hierarchical Navigable Small World
    

class MetricType(str, Enum):
    """Distance metrics"""
    L2 = "L2"  # Euclidean distance
    COSINE = "COSINE"  # Cosine similarity
    IP = "IP"  # Inner product


@dataclass
class VectorDocument:
    """
    Document with vector embedding
    """
    # Unique identifier
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Vector embedding
    vector: Optional[np.ndarray] = None
    dimension: int = 768
    
    # Metadata
    tenant_id: str = ""
    title: str = ""
    content: Optional[str] = None
    source: str = ""
    url: Optional[str] = None
    
    # Document metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Versioning
    version: int = 1
    
    # Soft delete flag
    is_deleted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding vector)"""
        return {
            "doc_id": self.doc_id,
            "tenant_id": self.tenant_id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "version": self.version,
            "is_deleted": self.is_deleted,
            "dimension": self.dimension,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorDocument":
        """Create from dictionary"""
        doc = cls(
            doc_id=data.get("doc_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", ""),
            title=data.get("title", ""),
            content=data.get("content"),
            source=data.get("source", ""),
            url=data.get("url"),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
            is_deleted=data.get("is_deleted", False),
            dimension=data.get("dimension", 768),
        )
        
        # Parse timestamps
        if data.get("created_at"):
            doc.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            doc.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("deleted_at"):
            doc.deleted_at = datetime.fromisoformat(data["deleted_at"])
        
        return doc


@dataclass
class VectorMetadata:
    """
    Lightweight metadata record for vector lookup
    """
    doc_id: str
    tenant_id: str
    title: str
    source: str
    url: Optional[str] = None
    version: int = 1
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Operation:
    """
    Operation log entry for WAL
    """
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: OperationType = OperationType.ADD
    doc_id: str = ""
    tenant_id: str = ""
    
    # Operation data
    vector_dimension: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Sequencing
    sequence_number: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Operation outcome
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "doc_id": self.doc_id,
            "tenant_id": self.tenant_id,
            "vector_dimension": self.vector_dimension,
            "metadata": self.metadata,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        """Create from dictionary"""
        op = cls(
            operation_id=data.get("operation_id", str(uuid.uuid4())),
            operation_type=OperationType(data.get("operation_type", "add")),
            doc_id=data.get("doc_id", ""),
            tenant_id=data.get("tenant_id", ""),
            vector_dimension=data.get("vector_dimension"),
            metadata=data.get("metadata"),
            sequence_number=data.get("sequence_number", 0),
            success=data.get("success", True),
            error=data.get("error"),
        )
        
        if data.get("timestamp"):
            op.timestamp = datetime.fromisoformat(data["timestamp"])
        
        return op


@dataclass
class IndexConfig:
    """
    FAISS index configuration
    """
    index_type: IndexType = IndexType.IVF_FLAT
    metric_type: MetricType = MetricType.L2
    dimension: int = 768
    
    # IVF parameters
    ivf_n_clusters: int = 100  # Number of clusters for IVF
    ivf_nprobe: int = 10  # Number of clusters to search
    
    # PQ parameters (for IVFPQ)
    pq_n_subquantizers: int = 8
    pq_bits_per_code: int = 8
    
    # HNSW parameters
    hnsw_m: int = 32  # Number of connections
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 128
    
    # General
    use_gpu: bool = False
    shard_count: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "index_type": self.index_type.value,
            "metric_type": self.metric_type.value,
            "dimension": self.dimension,
            "ivf_n_clusters": self.ivf_n_clusters,
            "ivf_nprobe": self.ivf_nprobe,
            "pq_n_subquantizers": self.pq_n_subquantizers,
            "pq_bits_per_code": self.pq_bits_per_code,
            "hnsw_m": self.hnsw_m,
            "hnsw_ef_construction": self.hnsw_ef_construction,
            "hnsw_ef_search": self.hnsw_ef_search,
            "use_gpu": self.use_gpu,
            "shard_count": self.shard_count,
        }


@dataclass
class Snapshot:
    """
    Index snapshot metadata
    """
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_type: str = "full"  # full or incremental
    
    # Files
    index_file: str = ""
    metadata_file: str = ""
    oplog_file: str = ""
    
    # Metadata
    vector_count: int = 0
    dimension: int = 768
    index_config: Optional[IndexConfig] = None
    embedding_model_version: str = ""
    
    # Operation log state
    oplog_offset: int = 0
    oplog_sequence: int = 0
    
    # Integrity
    checksum: str = ""  # SHA256 hash
    file_size_bytes: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Storage location
    storage_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_type": self.snapshot_type,
            "index_file": self.index_file,
            "metadata_file": self.metadata_file,
            "oplog_file": self.oplog_file,
            "vector_count": self.vector_count,
            "dimension": self.dimension,
            "index_config": self.index_config.to_dict() if self.index_config else None,
            "embedding_model_version": self.embedding_model_version,
            "oplog_offset": self.oplog_offset,
            "oplog_sequence": self.oplog_sequence,
            "checksum": self.checksum,
            "file_size_bytes": self.file_size_bytes,
            "created_at": self.created_at.isoformat(),
            "storage_path": self.storage_path,
        }


@dataclass
class SearchResult:
    """
    Search result with metadata
    """
    doc_id: str
    score: float
    metadata: Optional[VectorMetadata] = None
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "doc_id": self.doc_id,
            "score": float(self.score),
            "rank": self.rank,
        }
        
        if self.metadata:
            result["metadata"] = {
                "tenant_id": self.metadata.tenant_id,
                "title": self.metadata.title,
                "source": self.metadata.source,
                "url": self.metadata.url,
                "version": self.metadata.version,
                "created_at": self.metadata.created_at.isoformat() if self.metadata.created_at else None,
            }
        
        return result

