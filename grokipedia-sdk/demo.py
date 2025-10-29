"""Quick demo of slug search feature"""

from grokipedia_sdk import Client

print('=== Grokipedia SDK - Slug Search Demo ===\n')

client = Client()

# Show total articles
total = client.get_total_article_count()
print(f'Total articles in index: {total:,}\n')

# Demo 1: Find specific article
query = 'python programming'
print(f'Searching for: "{query}"')
results = client.search_slug(query, limit=5)
print(f'Found {len(results)} results:')
for i, r in enumerate(results, 1):
    print(f'  {i}. {r}')

# Demo 2: Best match
print(f'\nBest match for "{query}":')
best = client.find_slug(query)
print(f'  -> {best}')

# Demo 3: List by prefix
print(f'\nArticles starting with "Python":')
python_articles = client.list_available_articles(prefix='Python', limit=5)
for i, a in enumerate(python_articles, 1):
    print(f'  {i}. {a}')

print('\n=== Demo Complete ===')

