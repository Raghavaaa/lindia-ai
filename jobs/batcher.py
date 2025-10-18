"""
Micro-Batching System
Batches compatible jobs together for efficient processing
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .models import Job, BatchRequest, JobType
import logging
import os

logger = logging.getLogger(__name__)


class Batcher:
    """
    Micro-batching system that groups compatible jobs
    Flushes on: time window expiry OR size limit reached
    """
    
    def __init__(self):
        # Configuration from environment
        self.max_batch_size = int(os.getenv("BATCH_MAX_SIZE", "10"))
        self.batch_window_ms = int(os.getenv("BATCH_WINDOW_MS", "100"))
        self.enabled = bool(os.getenv("BATCH_ENABLED", "true").lower() == "true")
        
        # Active batches by (provider, job_type)
        self._batches: Dict[tuple, BatchRequest] = {}
        self._batch_timers: Dict[tuple, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        
        logger.info(
            f"Batcher initialized: max_size={self.max_batch_size}, "
            f"window={self.batch_window_ms}ms, enabled={self.enabled}"
        )
    
    async def add_job(self, job: Job, flush_callback) -> bool:
        """
        Add job to appropriate batch
        
        Args:
            job: Job to batch
            flush_callback: Async function to call when batch is ready
            
        Returns:
            True if added to batch, False if should process immediately
        """
        if not self.enabled:
            return False
        
        async with self._lock:
            # Determine batch key
            provider = job.target_provider or "default"
            batch_key = (provider, job.job_type)
            
            # Get or create batch
            if batch_key not in self._batches:
                batch = BatchRequest(
                    provider=provider,
                    job_type=job.job_type
                )
                self._batches[batch_key] = batch
                
                # Start timer for this batch
                timer = asyncio.create_task(
                    self._batch_timer(batch_key, flush_callback)
                )
                self._batch_timers[batch_key] = timer
            else:
                batch = self._batches[batch_key]
            
            # Add job to batch
            batch.add_job(job)
            
            logger.debug(
                f"Added job {job.job_id} to batch {batch.batch_id}, "
                f"size={batch.size()}/{self.max_batch_size}"
            )
            
            # Check if batch is full
            if batch.size() >= self.max_batch_size:
                logger.info(f"Batch {batch.batch_id} reached max size, flushing")
                await self._flush_batch(batch_key, flush_callback)
            
            return True
    
    async def _batch_timer(self, batch_key: tuple, flush_callback):
        """Timer that flushes batch after time window"""
        try:
            # Wait for time window
            await asyncio.sleep(self.batch_window_ms / 1000.0)
            
            # Flush batch
            async with self._lock:
                if batch_key in self._batches:
                    batch = self._batches[batch_key]
                    logger.info(
                        f"Batch {batch.batch_id} time window expired, "
                        f"flushing with {batch.size()} jobs"
                    )
                    await self._flush_batch(batch_key, flush_callback)
        
        except asyncio.CancelledError:
            logger.debug(f"Batch timer cancelled for {batch_key}")
        except Exception as e:
            logger.error(f"Batch timer error: {e}")
    
    async def _flush_batch(self, batch_key: tuple, flush_callback):
        """
        Flush batch and process jobs
        Note: Must be called with lock held
        """
        if batch_key not in self._batches:
            return
        
        batch = self._batches.pop(batch_key)
        
        # Cancel timer
        if batch_key in self._batch_timers:
            self._batch_timers[batch_key].cancel()
            del self._batch_timers[batch_key]
        
        # Process batch if not empty
        if batch.jobs:
            # Call flush callback asynchronously
            asyncio.create_task(flush_callback(batch))
    
    async def force_flush_all(self, flush_callback):
        """Force flush all pending batches (for shutdown)"""
        async with self._lock:
            batch_keys = list(self._batches.keys())
            for batch_key in batch_keys:
                await self._flush_batch(batch_key, flush_callback)
    
    async def get_stats(self) -> Dict:
        """Get batching statistics"""
        async with self._lock:
            return {
                "enabled": self.enabled,
                "max_batch_size": self.max_batch_size,
                "batch_window_ms": self.batch_window_ms,
                "active_batches": len(self._batches),
                "batch_details": [
                    {
                        "provider": batch.provider,
                        "job_type": batch.job_type.value,
                        "size": batch.size(),
                        "age_ms": (datetime.utcnow() - batch.created_at).total_seconds() * 1000
                    }
                    for batch in self._batches.values()
                ]
            }

