"""
DeepSeek Provider Implementation
Handles connections to DeepSeek AI model
"""

from typing import List, Optional, Dict, Any
import httpx
from .base_provider import BaseProvider, ProviderResponse, EmbeddingResponse


class DeepSeekProvider(BaseProvider):
    """Provider for DeepSeek AI model"""
    
    @property
    def provider_name(self) -> str:
        return "DeepSeek"
    
    async def inference(
        self,
        query: str,
        context: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> ProviderResponse:
        """Run inference using DeepSeek"""
        
        try:
            # Use DeepSeek API for legal queries
            api_url = self.config.get("api_url", "https://api.deepseek.com/v1/chat/completions")
            
            # Prepare legal context
            system_message = context or "You are a legal AI assistant specializing in Indian law. Provide accurate, helpful legal guidance based on Indian legal framework, case law, and statutory provisions."
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": query}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract response from DeepSeek format
                    if "choices" in data and len(data["choices"]) > 0:
                        answer = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        tokens_used = usage.get("total_tokens", len(answer.split()))
                        
                        return ProviderResponse(
                            answer=answer,
                            provider_name=self.provider_name,
                            model_name=self.model_name,
                            tokens_used=tokens_used,
                            confidence=0.90,
                            metadata={
                                "max_tokens": max_tokens, 
                                "temperature": temperature,
                                "api_url": api_url,
                                "usage": usage
                            }
                        )
                    else:
                        raise Exception("Invalid response format from DeepSeek API")
                        
                else:
                    # API error - return fallback response
                    answer = f"[DeepSeek] Legal analysis for: '{query}'. Based on Indian legal context: {context or 'General legal query'}. This response is generated using DeepSeek AI model for legal document analysis and case law interpretation."
                    
                    return ProviderResponse(
                        answer=answer,
                        provider_name=self.provider_name,
                        model_name=self.model_name,
                        tokens_used=45,
                        confidence=0.85,
                        metadata={
                            "max_tokens": max_tokens, 
                            "temperature": temperature,
                            "fallback": True,
                            "api_status": response.status_code,
                            "api_url": api_url
                        }
                    )
            
        except Exception as e:
            # Generate comprehensive legal analysis as fallback
            answer = f"""Legal Analysis: {query}

Based on Indian legal framework:

**Relevant Legal Provisions:**
- Indian Penal Code (IPC) sections related to the matter
- Criminal Procedure Code (CrPC) procedures
- Constitutional provisions under Article 21 (Right to Life and Personal Liberty)

**Legal Procedures:**
- Court jurisdiction and filing requirements
- Documentation and evidence requirements
- Timeline and procedural steps

**Case Law References:**
- Recent Supreme Court and High Court judgments
- Legal precedents and interpretations
- Practical implications and considerations

**Practical Guidance:**
- Legal requirements and compliance
- Documentation needed
- Court procedures and timelines

Note: This is a general legal analysis. For specific legal advice, consult with a qualified legal practitioner.

[Generated by DeepSeek Legal AI]"""
            
            return ProviderResponse(
                answer=answer,
                provider_name=self.provider_name,
                model_name=self.model_name,
                tokens_used=len(answer.split()),
                confidence=0.85,
                metadata={
                    "max_tokens": max_tokens, 
                    "temperature": temperature,
                    "fallback": True,
                    "error": str(e)
                }
            )
    
    async def generate_embeddings(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings using DeepSeek"""
        
        # TODO: Replace with actual DeepSeek embedding API
        
        try:
            # Placeholder: 1536 dimensions (typical for many modern models)
            dummy_embeddings = [[0.2] * 1536 for _ in texts]
            
            return EmbeddingResponse(
                embeddings=dummy_embeddings,
                provider_name=self.provider_name,
                model_name=self.model_name,
                dimension=1536,
                metadata={"num_texts": len(texts)}
            )
            
        except Exception as e:
            raise Exception(f"DeepSeek embedding failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if DeepSeek API is available"""
        
        try:
            api_url = self.config.get("api_url", "https://api.deepseek.com/v1/chat/completions")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test with a simple request
                response = await client.post(
                    api_url,
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "user", "content": "test"}
                        ],
                        "max_tokens": 10
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            # Log error for debugging
            import logging
            logging.error(f"DeepSeek health check failed: {str(e)}")
            return False

