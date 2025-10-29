"""Slug index for fast article lookup"""

from pathlib import Path
from typing import List, Optional, Dict, Tuple
from difflib import SequenceMatcher
import asyncio


class SlugIndex:
    """Index of available article slugs from sitemap"""
    
    def __init__(self, links_dir: Optional[Path] = None):
        """
        Initialize slug index.
        
        Args:
            links_dir: Path to links directory (default: auto-detect)
        """
        if links_dir is None:
            # Auto-detect links directory relative to this file
            sdk_dir = Path(__file__).parent
            links_dir = sdk_dir / "links"
        
        self.links_dir = Path(links_dir)
        self._index: Optional[Dict[str, str]] = None
        self._all_slugs: Optional[List[str]] = None
    
    @staticmethod
    def _normalize_name(slug: str) -> str:
        """
        Normalize a slug for lookup.
        
        Converts to lowercase and replaces underscores with spaces.
        This allows flexible matching across different formats.
        
        Args:
            slug: The slug to normalize
            
        Returns:
            Normalized slug (lowercase, underscores → spaces)
            
        Example:
            >>> SlugIndex._normalize_name("Joe_Biden")
            'joe biden'
        """
        return slug.lower().replace('_', ' ')
    
    def load(self) -> Dict[str, str]:
        """
        Load the slug index from sitemap files.
        
        Returns:
            Dictionary mapping normalized names to slugs
        """
        if self._index is not None:
            return self._index
        
        self._index = {}
        unique_slugs = set()
        
        if not self.links_dir.exists():
            return self._index
        
        # Load all sitemap files
        for sitemap_dir in sorted(self.links_dir.glob("sitemap-*")):
            names_file = sitemap_dir / "names.txt"
            if names_file.exists():
                try:
                    with open(names_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            slug = line.strip()
                            if slug:
                                unique_slugs.add(slug)
                                # Store normalized version for flexible matching
                                normalized = self._normalize_name(slug)
                                self._index[normalized] = slug
                                # Also store the lowercase original for exact matches
                                self._index[slug.lower()] = slug
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        # Store sorted list of all unique slugs
        self._all_slugs = sorted(unique_slugs)
        
        return self._index
    
    async def load_async(self) -> Dict[str, str]:
        """
        Load the slug index from sitemap files asynchronously.
        
        Useful when integrating with async frameworks or when loading
        from slow I/O sources. For typical local file systems, the
        synchronous load() method is recommended.
        
        Returns:
            Dictionary mapping normalized names to slugs
            
        Example:
            >>> index = SlugIndex()
            >>> index_dict = await index.load_async()
        """
        # Run the blocking load() in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.load)
    
    def search(self, query: str, limit: int = 10, fuzzy: bool = True, min_similarity: float = 0.6) -> List[str]:
        """
        Search for matching slugs.
        
        Args:
            query: Search query (can use spaces or underscores)
            limit: Maximum number of results to return
            fuzzy: Enable fuzzy matching if no exact matches found
            min_similarity: Minimum similarity score for fuzzy matching (0.0 to 1.0)
            
        Returns:
            List of matching slugs, ordered by relevance
            
        Example:
            >>> index = SlugIndex()
            >>> index.search("joe biden")
            ['Joe_Biden', 'Joe_Biden_presidential_campaign', ...]
        """
        index = self.load()
        query_normalized = self._normalize_name(query)
        
        # Strategy 1: Exact substring matches (case-insensitive)
        matches = []
        seen = set()
        
        for normalized_name, slug in index.items():
            if query_normalized in normalized_name:
                if slug not in seen:
                    matches.append(slug)
                    seen.add(slug)
                    if len(matches) >= limit:
                        break
        
        # Strategy 2: Fuzzy matching if enabled and we don't have enough matches
        if fuzzy and len(matches) < limit:
            similarities: List[Tuple[float, str]] = []
            
            for normalized_name, slug in index.items():
                if slug in seen:
                    continue  # Skip already matched slugs
                
                # Calculate similarity ratio
                similarity = SequenceMatcher(None, query_normalized, normalized_name).ratio()
                
                if similarity >= min_similarity:
                    similarities.append((similarity, slug))
            
            # Sort by similarity (highest first) and add top matches
            similarities.sort(reverse=True, key=lambda x: x[0])
            
            remaining = limit - len(matches)
            for _, slug in similarities[:remaining]:
                if slug not in seen:
                    matches.append(slug)
                    seen.add(slug)
        
        return matches
    
    def find_best_match(self, query: str, min_similarity: float = 0.6) -> Optional[str]:
        """
        Find the single best matching slug for a query.
        
        Args:
            query: Article name or partial slug
            min_similarity: Minimum similarity score for fuzzy matching
            
        Returns:
            Best matching slug or None if not found
            
        Example:
            >>> index = SlugIndex()
            >>> index.find_best_match("elon musk")
            'Elon_Musk'
        """
        results = self.search(query, limit=1, fuzzy=True, min_similarity=min_similarity)
        return results[0] if results else None
    
    def exists(self, slug: str) -> bool:
        """
        Check if a slug exists in the index.
        
        Args:
            slug: Slug to check
            
        Returns:
            True if slug exists, False otherwise
            
        Example:
            >>> index = SlugIndex()
            >>> index.exists("Joe_Biden")
            True
        """
        index = self.load()
        slug_lower = slug.lower()
        
        # Check both normalized and original forms
        return slug_lower in index or slug in set(index.values())
    
    def list_by_prefix(self, prefix: str = "", limit: int = 100) -> List[str]:
        """
        List available articles, optionally filtered by prefix.
        
        Args:
            prefix: Filter articles starting with this prefix (case-insensitive)
            limit: Maximum number of results
            
        Returns:
            List of article slugs matching the prefix
            
        Example:
            >>> index = SlugIndex()
            >>> index.list_by_prefix(prefix="Artificial", limit=20)
            ['Artificial_Intelligence', 'Artificial_Neural_Network', ...]
        """
        self.load()  # Ensure index is loaded
        
        if not self._all_slugs:
            return []
        
        prefix_lower = prefix.lower()
        matches = []
        
        for slug in self._all_slugs:
            if slug.lower().startswith(prefix_lower):
                matches.append(slug)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_total_count(self) -> int:
        """
        Get the total number of articles in the index.
        
        Returns:
            Total number of unique article slugs
        """
        self.load()
        return len(self._all_slugs) if self._all_slugs else 0
    
    def random_slugs(self, count: int = 10) -> List[str]:
        """
        Get random article slugs from the index.
        
        Args:
            count: Number of random slugs to return
            
        Returns:
            List of random slugs
        """
        import random
        
        self.load()
        
        if not self._all_slugs:
            return []
        
        # Don't try to sample more than available
        sample_size = min(count, len(self._all_slugs))
        return random.sample(self._all_slugs, sample_size)

