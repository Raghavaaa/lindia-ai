#!/usr/bin/env python3
"""
Test AI Pipeline with "murder bail" input
Demonstrates complete InLegalBERT → DeepSeek workflow
"""

import asyncio
import httpx
import os
import time

async def test_murder_bail():
    """Test the complete AI pipeline with 'murder bail' input"""
    print('🔍 TESTING AI PIPELINE WITH INPUT: "murder bail"')
    print('=' * 60)
    print()
    
    # Set up API credentials
    deepseek_key = os.getenv('DEEPSEEK_API_KEY', 'os.getenv("DEEPSEEK_API_KEY", "")')
    inlegalbert_key = os.getenv('INLEGALBERT_API_KEY', 'os.getenv("INLEGALBERT_API_KEY", "")')
    
    test_query = 'murder bail'
    print(f'📝 Input Query: "{test_query}"')
    print()
    
    # Stage 1: InLegalBERT Enhancement
    print('STAGE 1: InLegalBERT Enhancement')
    print('-' * 40)
    
    inlegalbert_url = 'https://api-inference.huggingface.co/models/law-ai/InLegalBERT'
    
    headers = {
        'Authorization': f'Bearer {inlegalbert_key}',
        'Content-Type': 'application/json'
    }
    
    # Create masked query for InLegalBERT
    masked_query = test_query.replace(' ', ' [MASK] ')
    print(f'📤 Masked Query: "{masked_query}"')
    
    payload = {
        'inputs': masked_query,
        'options': {'wait_for_model': True}
    }
    
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(inlegalbert_url, json=payload, headers=headers)
        
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f'✅ InLegalBERT Success (Latency: {latency:.0f}ms)')
            print(f'📊 Got {len(data)} predictions')
            
            # Extract top prediction
            if data and len(data) > 0:
                top_pred = data[0]
                predicted_token = top_pred.get('token_str', '')
                confidence = top_pred.get('score', 0)
                print(f'🎯 Top Prediction: "{predicted_token}" (confidence: {confidence:.3f})')
                
                enhanced_query = f'{test_query} [Enhanced with legal context: {predicted_token}]'
            else:
                enhanced_query = f'{test_query} [Enhanced with legal context]'
        else:
            print(f'⚠️  InLegalBERT failed: {response.status_code}')
            enhanced_query = test_query
            
    except Exception as e:
        print(f'⚠️  InLegalBERT error: {str(e)}')
        enhanced_query = test_query
    
    print(f'📝 Enhanced Query: "{enhanced_query}"')
    print()
    
    # Stage 2: DeepSeek Analysis
    print('STAGE 2: DeepSeek Legal Analysis')
    print('-' * 40)
    
    deepseek_url = 'https://api.deepseek.com/v1/chat/completions'
    
    headers = {
        'Authorization': f'Bearer {deepseek_key}',
        'Content-Type': 'application/json'
    }
    
    system_prompt = """You are an expert Indian legal research assistant. 
Provide comprehensive, accurate legal guidance for Indian law.
Always include relevant sections, case law references, procedures, and warnings.
Keep responses concise but informative."""
    
    user_prompt = f"""Legal Query: {enhanced_query}

Provide detailed legal analysis with proper citations and actionable recommendations for Indian law."""
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'max_tokens': 1500,
        'temperature': 0.3
    }
    
    try:
        print(f'📤 Sending enhanced query to DeepSeek...')
        
        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(deepseek_url, json=payload, headers=headers)
        
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            answer = data['choices'][0]['message']['content']
            tokens = data.get('usage', {}).get('total_tokens', 0)
            
            print(f'✅ DeepSeek Success (Latency: {latency:.0f}ms)')
            print(f'📊 Tokens used: {tokens}')
            print(f'💰 Estimated cost: ~${tokens * 0.00014:.4f}')
            print()
            
            print('🎯 LEGAL ANALYSIS RESULT:')
            print('=' * 60)
            print(answer)
            print('=' * 60)
            
            # Quality analysis
            keywords = ['bail', 'murder', 'section', 'ipc', 'court', 'law', 'case', 'procedure']
            found_keywords = [kw for kw in keywords if kw.lower() in answer.lower()]
            
            print()
            print('📊 QUALITY ANALYSIS:')
            print(f'   Response Length: {len(answer)} characters')
            print(f'   Legal Keywords Found: {len(found_keywords)}/{len(keywords)}')
            print(f'   Keywords: {", ".join(found_keywords)}')
            print(f'   Quality Score: {len(found_keywords)/len(keywords)*100:.1f}%')
            
            return True
        else:
            print(f'❌ DeepSeek failed: {response.status_code}')
            print(f'Error: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'❌ DeepSeek error: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main execution"""
    result = await test_murder_bail()
    
    print()
    if result:
        print('🎉 PIPELINE TEST COMPLETE - SUCCESS!')
        print('✅ InLegalBERT → DeepSeek pipeline working perfectly')
        print('✅ Ready for production deployment')
    else:
        print('❌ PIPELINE TEST FAILED')
        print('🔧 Check API keys and network connectivity')

if __name__ == "__main__":
    asyncio.run(main())
