"""
Job Storage - Status, Results, and Dead Letter Queue
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .models import Job, JobStatus, JobResult
import logging

logger = logging.getLogger(__name__)


class JobStorage:
    """
    Stores job status, results, and manages dead letter queue
    Supports in-memory (dev) and Redis (prod)
    """
    
    def __init__(self, backend: str = "memory", redis_client=None, ttl_hours: int = 24):
        self.backend = backend
        self.redis = redis_client
        self.ttl_seconds = ttl_hours * 3600
        
        # In-memory storage
        self._jobs: Dict[str, Job] = {}
        self._results: Dict[str, JobResult] = {}
        self._dlq: Dict[str, Job] = {}  # Dead letter queue
        self._idempotency: Dict[str, str] = {}  # idempotency_key -> job_id
        self._lock = asyncio.Lock()
    
    async def save_job(self, job: Job) -> bool:
        """Save or update job"""
        try:
            if self.backend == "redis" and self.redis:
                await self._save_job_redis(job)
            else:
                await self._save_job_memory(job)
            return True
        except Exception as e:
            logger.error(f"Failed to save job {job.job_id}: {e}")
            return False
    
    async def _save_job_memory(self, job: Job):
        """Save to in-memory storage"""
        async with self._lock:
            self._jobs[job.job_id] = job
            if job.idempotency_key:
                self._idempotency[job.idempotency_key] = job.job_id
    
    async def _save_job_redis(self, job: Job):
        """Save to Redis"""
        key = f"job:{job.job_id}"
        await self.redis.setex(key, self.ttl_seconds, json.dumps(job.to_dict()))
        
        if job.idempotency_key:
            idem_key = f"idem:{job.idempotency_key}"
            await self.redis.setex(idem_key, self.ttl_seconds, job.job_id)
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID"""
        try:
            if self.backend == "redis" and self.redis:
                return await self._get_job_redis(job_id)
            else:
                return await self._get_job_memory(job_id)
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    async def _get_job_memory(self, job_id: str) -> Optional[Job]:
        """Get from in-memory storage"""
        async with self._lock:
            return self._jobs.get(job_id)
    
    async def _get_job_redis(self, job_id: str) -> Optional[Job]:
        """Get from Redis"""
        key = f"job:{job_id}"
        data = await self.redis.get(key)
        if data:
            return Job.from_dict(json.loads(data))
        return None
    
    async def check_idempotency(self, idempotency_key: str) -> Optional[str]:
        """Check if idempotency key exists, return job_id if found"""
        try:
            if self.backend == "redis" and self.redis:
                idem_key = f"idem:{idempotency_key}"
                job_id = await self.redis.get(idem_key)
                return job_id.decode() if job_id else None
            else:
                async with self._lock:
                    return self._idempotency.get(idempotency_key)
        except Exception as e:
            logger.error(f"Failed to check idempotency: {e}")
            return None
    
    async def save_result(self, result: JobResult) -> bool:
        """Save job result"""
        try:
            if self.backend == "redis" and self.redis:
                key = f"result:{result.job_id}"
                await self.redis.setex(key, self.ttl_seconds, json.dumps(result.to_dict()))
            else:
                async with self._lock:
                    self._results[result.job_id] = result
            return True
        except Exception as e:
            logger.error(f"Failed to save result for {result.job_id}: {e}")
            return False
    
    async def get_result(self, job_id: str) -> Optional[JobResult]:
        """Get job result"""
        try:
            if self.backend == "redis" and self.redis:
                key = f"result:{job_id}"
                data = await self.redis.get(key)
                if data:
                    result_dict = json.loads(data)
                    return JobResult(**result_dict)
                return None
            else:
                async with self._lock:
                    return self._results.get(job_id)
        except Exception as e:
            logger.error(f"Failed to get result for {job_id}: {e}")
            return None
    
    async def add_to_dlq(self, job: Job, error: str):
        """Add failed job to dead letter queue"""
        try:
            job.status = JobStatus.DEAD_LETTER
            job.error = error
            
            if self.backend == "redis" and self.redis:
                key = f"dlq:{job.job_id}"
                await self.redis.setex(key, self.ttl_seconds * 7, json.dumps(job.to_dict()))  # Longer TTL for DLQ
            else:
                async with self._lock:
                    self._dlq[job.job_id] = job
            
            logger.warning(f"Job {job.job_id} added to dead letter queue: {error}")
            return True
        except Exception as e:
            logger.error(f"Failed to add job to DLQ: {e}")
            return False
    
    async def get_dlq_jobs(self, limit: int = 100) -> List[Job]:
        """Get jobs from dead letter queue"""
        try:
            if self.backend == "redis" and self.redis:
                keys = await self.redis.keys("dlq:*")
                jobs = []
                for key in keys[:limit]:
                    data = await self.redis.get(key)
                    if data:
                        jobs.append(Job.from_dict(json.loads(data)))
                return jobs
            else:
                async with self._lock:
                    return list(self._dlq.values())[:limit]
        except Exception as e:
            logger.error(f"Failed to get DLQ jobs: {e}")
            return []
    
    async def requeue_from_dlq(self, job_id: str) -> Optional[Job]:
        """Remove job from DLQ for reprocessing"""
        try:
            if self.backend == "redis" and self.redis:
                key = f"dlq:{job_id}"
                data = await self.redis.get(key)
                if data:
                    await self.redis.delete(key)
                    job = Job.from_dict(json.loads(data))
                    job.status = JobStatus.PENDING
                    job.attempt_count = 0
                    job.error = None
                    return job
                return None
            else:
                async with self._lock:
                    job = self._dlq.pop(job_id, None)
                    if job:
                        job.status = JobStatus.PENDING
                        job.attempt_count = 0
                        job.error = None
                    return job
        except Exception as e:
            logger.error(f"Failed to requeue from DLQ: {e}")
            return None
    
    async def update_status(self, job_id: str, status: JobStatus, error: Optional[str] = None):
        """Update job status"""
        job = await self.get_job(job_id)
        if job:
            job.status = status
            if error:
                job.error = error
            if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
                job.completed_at = datetime.utcnow()
            await self.save_job(job)
    
    async def cleanup_old_jobs(self, hours: int = 24):
        """Clean up old completed jobs (memory only)"""
        if self.backend != "memory":
            return  # Redis handles TTL automatically
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        async with self._lock:
            to_remove = [
                job_id for job_id, job in self._jobs.items()
                if job.completed_at and job.completed_at < cutoff
            ]
            for job_id in to_remove:
                del self._jobs[job_id]
                self._results.pop(job_id, None)
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old jobs")

