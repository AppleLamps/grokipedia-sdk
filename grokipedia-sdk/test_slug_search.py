"""Quick test script for slug search functionality"""

from grokipedia_sdk import Client

def test_slug_search():
    client = Client()

    # Test 1: Search
    print('Test 1: Search for "joe biden"')
    results = client.search_slug('joe biden', limit=5)
    for r in results[:3]:
        print(f'  - {r}')

    # Test 2: Find best match
    print('\nTest 2: Find best match for "artificial intelligence"')
    slug = client.find_slug('artificial intelligence')
    print(f'  Found: {slug}')

    # Test 3: Check existence
    print('\nTest 3: Check if slug exists')
    print(f'  Joe_Biden exists: {client.slug_exists("Joe_Biden")}')
    print(f'  Fake_Article exists: {client.slug_exists("Fake_Article_12345")}')

    # Test 4: List by prefix
    print('\nTest 4: List articles by prefix "Climate"')
    articles = client.list_available_articles(prefix='Climate', limit=5)
    for a in articles:
        print(f'  - {a}')

    # Test 5: Random articles
    print('\nTest 5: Random articles')
    random = client.get_random_articles(3)
    for r in random:
        print(f'  - {r}')
    
    # Test 6: Total count
    print(f'\nTest 6: Total articles in index: {client.get_total_article_count():,}')

    print('\nAll tests passed!')

if __name__ == '__main__':
    test_slug_search()

