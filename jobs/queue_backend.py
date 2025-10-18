"""
Queue Backend Implementations
Supports in-memory (dev) and Redis (prod)
"""

import asyncio
import heapq
import json
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from .models import Job, Priority
import logging

logger = logging.getLogger(__name__)


class QueueBackend(ABC):
    """Abstract queue backend"""
    
    @abstractmethod
    async def enqueue(self, job: Job) -> bool:
        """Add job to queue"""
        pass
    
    @abstractmethod
    async def dequeue(self) -> Optional[Job]:
        """Get next job from queue"""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get queue size"""
        pass
    
    @abstractmethod
    async def peek(self) -> Optional[Job]:
        """Peek at next job without removing"""
        pass
    
    @abstractmethod
    async def remove(self, job_id: str) -> bool:
        """Remove specific job"""
        pass


class InMemoryQueue(QueueBackend):
    """
    In-memory priority queue for development
    Uses heapq for FIFO with priority support
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: List[tuple] = []  # (priority_int, timestamp, job)
        self._lock = asyncio.Lock()
        self._counter = 0  # For FIFO within same priority
    
    async def enqueue(self, job: Job) -> bool:
        """Add job to priority queue"""
        async with self._lock:
            if len(self._queue) >= self.max_size:
                logger.warning(f"Queue at max capacity ({self.max_size}), rejecting job {job.job_id}")
                return False
            
            # Higher priority number = processed first (reverse for heapq)
            priority_int = -job.priority.to_int()
            
            # Use counter for FIFO within same priority
            heapq.heappush(self._queue, (priority_int, self._counter, job))
            self._counter += 1
            
            logger.debug(f"Enqueued job {job.job_id} with priority {job.priority.value}")
            return True
    
    async def dequeue(self) -> Optional[Job]:
        """Get highest priority job"""
        async with self._lock:
            if not self._queue:
                return None
            
            _, _, job = heapq.heappop(self._queue)
            logger.debug(f"Dequeued job {job.job_id}")
            return job
    
    async def size(self) -> int:
        """Get current queue size"""
        async with self._lock:
            return len(self._queue)
    
    async def peek(self) -> Optional[Job]:
        """Look at next job without removing"""
        async with self._lock:
            if not self._queue:
                return None
            return self._queue[0][2]
    
    async def remove(self, job_id: str) -> bool:
        """Remove specific job by ID"""
        async with self._lock:
            original_size = len(self._queue)
            self._queue = [(p, c, j) for p, c, j in self._queue if j.job_id != job_id]
            heapq.heapify(self._queue)
            removed = len(self._queue) < original_size
            if removed:
                logger.debug(f"Removed job {job_id} from queue")
            return removed


class RedisQueue(QueueBackend):
    """
    Redis-based queue for production
    Uses sorted sets for priority + FIFO ordering
    """
    
    def __init__(self, redis_client, key_prefix: str = "ai_job_queue", max_size: int = 100000):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.max_size = max_size
        self._queue_key = f"{key_prefix}:jobs"
        self._counter_key = f"{key_prefix}:counter"
    
    async def enqueue(self, job: Job) -> bool:
        """Add job to Redis sorted set"""
        try:
            # Check size
            current_size = await self.redis.zcard(self._queue_key)
            if current_size >= self.max_size:
                logger.warning(f"Redis queue at max capacity ({self.max_size}), rejecting job {job.job_id}")
                return False
            
            # Generate score: priority (higher = first) + counter for FIFO
            counter = await self.redis.incr(self._counter_key)
            priority_score = job.priority.to_int() * 1000000000  # Large multiplier for priority
            score = -priority_score + counter  # Negative for reverse sort
            
            # Serialize job
            job_data = json.dumps(job.to_dict())
            
            # Add to sorted set
            await self.redis.zadd(self._queue_key, {job_data: score})
            
            logger.debug(f"Enqueued job {job.job_id} to Redis with priority {job.priority.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue job to Redis: {e}")
            return False
    
    async def dequeue(self) -> Optional[Job]:
        """Get highest priority job from Redis"""
        try:
            # Pop lowest score (highest priority)
            result = await self.redis.zpopmin(self._queue_key)
            if not result:
                return None
            
            job_data, score = result[0]
            job_dict = json.loads(job_data)
            job = Job.from_dict(job_dict)
            
            logger.debug(f"Dequeued job {job.job_id} from Redis")
            return job
            
        except Exception as e:
            logger.error(f"Failed to dequeue job from Redis: {e}")
            return None
    
    async def size(self) -> int:
        """Get current queue size"""
        try:
            return await self.redis.zcard(self._queue_key)
        except Exception as e:
            logger.error(f"Failed to get Redis queue size: {e}")
            return 0
    
    async def peek(self) -> Optional[Job]:
        """Look at next job without removing"""
        try:
            result = await self.redis.zrange(self._queue_key, 0, 0)
            if not result:
                return None
            
            job_dict = json.loads(result[0])
            return Job.from_dict(job_dict)
            
        except Exception as e:
            logger.error(f"Failed to peek Redis queue: {e}")
            return None
    
    async def remove(self, job_id: str) -> bool:
        """Remove specific job by ID"""
        try:
            # Scan all jobs and remove matching ID
            all_jobs = await self.redis.zrange(self._queue_key, 0, -1)
            for job_data in all_jobs:
                job_dict = json.loads(job_data)
                if job_dict.get("job_id") == job_id:
                    await self.redis.zrem(self._queue_key, job_data)
                    logger.debug(f"Removed job {job_id} from Redis queue")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove job from Redis: {e}")
            return False

