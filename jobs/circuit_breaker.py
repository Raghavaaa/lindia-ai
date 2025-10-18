"""
Circuit Breaker Implementation Per Provider
Prevents cascading failures by short-circuiting calls to failing providers
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from .models import CircuitBreakerState
import logging
import os

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker for individual provider
    States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing) -> CLOSED/OPEN
    """
    
    def __init__(
        self,
        provider_name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3
    ):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitBreakerState(provider_name=provider_name)
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def is_available(self) -> bool:
        """Check if provider is available for calls"""
        async with self._lock:
            if self.state.is_closed():
                return True
            
            if self.state.is_open():
                # Check if timeout has passed to try half-open
                if self.state.opened_at:
                    elapsed = (datetime.utcnow() - self.state.opened_at).total_seconds()
                    if elapsed >= self.timeout_seconds:
                        # Transition to half-open
                        self.state.state = "half_open"
                        self.half_open_calls = 0
                        logger.info(f"Circuit breaker for {self.provider_name} transitioning to HALF_OPEN")
                        return True
                return False
            
            if self.state.is_half_open():
                # Allow limited calls in half-open state
                if self.half_open_calls < self.half_open_max_calls:
                    return True
                return False
            
            return False
    
    async def record_success(self):
        """Record successful call"""
        async with self._lock:
            self.state.success_count += 1
            
            if self.state.is_half_open():
                self.half_open_calls += 1
                # Check if we can close the circuit
                if self.state.success_count >= self.success_threshold:
                    self.state.state = "closed"
                    self.state.failure_count = 0
                    self.state.success_count = 0
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker for {self.provider_name} CLOSED after recovery")
            
            elif self.state.is_closed():
                # Reset failure count on success
                self.state.failure_count = 0
    
    async def record_failure(self):
        """Record failed call"""
        async with self._lock:
            self.state.failure_count += 1
            self.state.last_failure_time = datetime.utcnow()
            
            if self.state.is_closed():
                # Check if we should open the circuit
                if self.state.failure_count >= self.failure_threshold:
                    self.state.state = "open"
                    self.state.opened_at = datetime.utcnow()
                    self.state.success_count = 0
                    logger.warning(
                        f"Circuit breaker for {self.provider_name} OPENED "
                        f"after {self.state.failure_count} failures"
                    )
            
            elif self.state.is_half_open():
                # Failed during half-open, reopen circuit
                self.state.state = "open"
                self.state.opened_at = datetime.utcnow()
                self.state.success_count = 0
                self.half_open_calls = 0
                logger.warning(f"Circuit breaker for {self.provider_name} REOPENED after failure during half-open")
    
    async def get_state(self) -> CircuitBreakerState:
        """Get current state"""
        async with self._lock:
            return CircuitBreakerState(
                provider_name=self.state.provider_name,
                state=self.state.state,
                failure_count=self.state.failure_count,
                success_count=self.state.success_count,
                last_failure_time=self.state.last_failure_time,
                opened_at=self.state.opened_at
            )


class CircuitBreakerManager:
    """
    Manages circuit breakers for all providers
    """
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
        
        # Load configuration from environment
        self.failure_threshold = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
        self.success_threshold = int(os.getenv("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "2"))
        self.timeout_seconds = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT_SECONDS", "60"))
        self.half_open_max_calls = int(os.getenv("CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS", "3"))
    
    async def get_breaker(self, provider_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider"""
        async with self._lock:
            if provider_name not in self.breakers:
                self.breakers[provider_name] = CircuitBreaker(
                    provider_name=provider_name,
                    failure_threshold=self.failure_threshold,
                    success_threshold=self.success_threshold,
                    timeout_seconds=self.timeout_seconds,
                    half_open_max_calls=self.half_open_max_calls
                )
                logger.info(f"Created circuit breaker for provider: {provider_name}")
            return self.breakers[provider_name]
    
    async def is_provider_available(self, provider_name: str) -> bool:
        """Check if provider is available"""
        breaker = await self.get_breaker(provider_name)
        return await breaker.is_available()
    
    async def record_success(self, provider_name: str):
        """Record success for provider"""
        breaker = await self.get_breaker(provider_name)
        await breaker.record_success()
    
    async def record_failure(self, provider_name: str):
        """Record failure for provider"""
        breaker = await self.get_breaker(provider_name)
        await breaker.record_failure()
    
    async def get_all_states(self) -> Dict[str, CircuitBreakerState]:
        """Get states of all circuit breakers"""
        states = {}
        async with self._lock:
            for provider_name, breaker in self.breakers.items():
                states[provider_name] = await breaker.get_state()
        return states
    
    async def reset(self, provider_name: str):
        """Manually reset a circuit breaker"""
        async with self._lock:
            if provider_name in self.breakers:
                del self.breakers[provider_name]
                logger.info(f"Reset circuit breaker for {provider_name}")

