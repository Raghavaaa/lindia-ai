#!/usr/bin/env python3
"""
Get Complete DeepSeek Output - Dowry Case
Retrieves and displays the full, untruncated response from DeepSeek
"""

import asyncio
import httpx
import os
import time

async def get_complete_deepseek_output():
    """Get the complete, untruncated DeepSeek output"""
    print('🔍 GETTING COMPLETE DEEPSEEK OUTPUT - DOWRY CASE')
    print('=' * 70)
    
    # Set up API credentials
    deepseek_key = 'os.getenv("DEEPSEEK_API_KEY", "")'
    inlegalbert_key = 'os.getenv("INLEGALBERT_API_KEY", "")'
    
    # Test query
    test_query = 'dowry case punishment procedure'
    print(f'📝 Input Query: "{test_query}"')
    print()
    
    # Stage 1: InLegalBERT Enhancement (quick)
    print('STAGE 1: InLegalBERT Enhancement')
    print('-' * 40)
    
    inlegalbert_url = 'https://api-inference.huggingface.co/models/law-ai/InLegalBERT'
    headers = {
        'Authorization': f'Bearer {inlegalbert_key}',
        'Content-Type': 'application/json'
    }
    
    masked_query = test_query.replace(' ', ' [MASK] ')
    payload = {
        'inputs': masked_query,
        'options': {'wait_for_model': True}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(inlegalbert_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            top_pred = data[0].get('token_str', '') if data else ''
            enhanced_query = f'{test_query} [Enhanced: {top_pred}]'
            print(f'✅ InLegalBERT Success - Enhanced: "{enhanced_query}"')
        else:
            enhanced_query = test_query
            print(f'⚠️  InLegalBERT failed, using original query')
    except:
        enhanced_query = test_query
        print(f'⚠️  InLegalBERT error, using original query')
    
    print()
    
    # Stage 2: DeepSeek Complete Analysis
    print('STAGE 2: DeepSeek Complete Analysis')
    print('-' * 40)
    
    deepseek_url = 'https://api.deepseek.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {deepseek_key}',
        'Content-Type': 'application/json'
    }
    
    system_prompt = """You are an expert Indian legal research assistant specializing in dowry-related cases. 
Provide comprehensive, accurate legal guidance for Indian law including:
- Relevant sections of IPC and Dowry Prohibition Act
- Punishments and procedures
- Case law and precedents
- Practical legal advice
- Court procedures and timelines

Always include proper citations, case references, and actionable recommendations."""
    
    user_prompt = f"""Legal Query: {enhanced_query}

Provide a comprehensive legal analysis of dowry cases in India, including:
1. Relevant laws and sections
2. Punishments and penalties
3. Legal procedures and court processes
4. Important case law and precedents
5. Practical legal advice for victims and accused
6. Court timelines and procedures
7. Recent amendments and developments

Make the analysis detailed, practical, and actionable for Indian legal practice."""
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'max_tokens': 4000,
        'temperature': 0.3
    }
    
    try:
        print('🚀 Calling DeepSeek API...')
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(deepseek_url, json=payload, headers=headers)
        
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            answer = data['choices'][0]['message']['content']
            tokens = data.get('usage', {}).get('total_tokens', 0)
            
            print(f'✅ DeepSeek Success!')
            print(f'📊 Tokens used: {tokens}')
            print(f'💰 Cost: ~${tokens * 0.00014:.4f}')
            print(f'⏱️  Latency: {latency:.0f}ms')
            print()
            
            # Save complete output to file
            with open('complete_deepseek_output.txt', 'w', encoding='utf-8') as f:
                f.write(f'COMPLETE DEEPSEEK OUTPUT - DOWRY CASE ANALYSIS\n')
                f.write(f'=' * 70 + '\n')
                f.write(f'Input Query: {test_query}\n')
                f.write(f'Enhanced Query: {enhanced_query}\n')
                f.write(f'Tokens Used: {tokens}\n')
                f.write(f'Cost: ~${tokens * 0.00014:.4f}\n')
                f.write(f'Latency: {latency:.0f}ms\n')
                f.write(f'=' * 70 + '\n\n')
                f.write(answer)
                f.write(f'\n\n' + '=' * 70 + '\n')
                f.write(f'END OF COMPLETE OUTPUT\n')
            
            print('📁 COMPLETE OUTPUT SAVED TO: complete_deepseek_output.txt')
            print()
            print('🎯 COMPLETE DEEPSEEK OUTPUT:')
            print('=' * 70)
            print(answer)
            print('=' * 70)
            
            return True
        else:
            print(f'❌ DeepSeek failed: {response.status_code}')
            print(f'Error: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return False

async def main():
    """Main execution"""
    result = await get_complete_deepseek_output()
    
    print()
    if result:
        print('🎉 COMPLETE OUTPUT RETRIEVED SUCCESSFULLY!')
        print('📁 Full output also saved to complete_deepseek_output.txt')
    else:
        print('❌ FAILED TO GET COMPLETE OUTPUT')

if __name__ == "__main__":
    asyncio.run(main())
