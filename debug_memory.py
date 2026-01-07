import os
from mem0 import MemoryClient

def debug():
    # Attempt to read from environment or default for debug
    api_key = os.environ.get('MEM0_API_KEY', 'm0-TqhAnGlqmJt3Gr6SaJ8z5iaPWYVcGxpiI67XC4Xo')
    print(f'Using API Key: {api_key[:5]}...')
    client = MemoryClient(api_key=api_key)
    
    agent_id = 'pc-win11-agent'
    
    print(f'Fetching all memories for {agent_id}...')
    try:
        mems = client.get_all(user_id=agent_id)
        if isinstance(mems, dict) and 'memories' in mems:
             mems = mems['memories']
        
        print(f'get_all count: {len(mems) if mems else 0}')
        if mems:
            for m in mems:
                print(f" - {m.get('memory')} (ID: {m.get('id')})")
    except Exception as e:
        print(f'get_all error: {e}')

    print(f'\nSearching for \"orchestrator\" with explicit filters for {agent_id}...')
    try:
        # Some versions of Mem0 Cloud require filters
        results = client.search('orchestrator', filters={"user_id": agent_id})
        if isinstance(results, dict) and 'results' in results:
            results = results['results']
        print(f'search (filters) count: {len(results) if results else 0}')
        if results:
            for r in results:
                print(f" - {r.get('memory')} (score: {r.get('score', 'N/A')})")
    except Exception as e:
        print(f'search (filters) error: {e}')

    print(f'\nSearching for \"orchestrator\" with user_id param...')
    try:
        results = client.search('orchestrator', user_id=agent_id)
        if hasattr(results, 'get') and 'results' in results: results = results['results']
        print(f'search (user_id) count: {len(results) if results else 0}')
    except Exception as e:
        print(f'search (user_id) error: {e}')

    print(f'\nVerifying specific memory IDs reported by Claude...')
    ids = ['d6bfca8f-6c2c-46bf-8120-8d4ab7f498ea', 'ed887820-893e-4de4-bff9-e77bbca76375']
    for mid in ids:
        try:
            print(f'Fetching memory ID: {mid}...')
            m = client.get(mid)
            if m:
                # Memory v2 usually returns a dict or object
                content = m.get('memory') if hasattr(m, 'get') else getattr(m, 'memory', str(m))
                user = m.get('user_id') if hasattr(m, 'get') else getattr(m, 'user_id', 'unknown')
                print(f" - Found: {content} (user: {user})")
            else:
                print(f" - Not found: {mid}")
        except Exception as e:
            print(f'Get by ID error for {mid}: {e}')

if __name__ == '__main__':
    debug()
