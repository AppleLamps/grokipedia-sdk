"""Slug index for fast article lookup"""

import asyncio
import heapq
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    # Fallback to difflib if rapidfuzz is not installed
    from difflib import SequenceMatcher
    HAS_RAPIDFUZZ = False
else:
    from difflib import SequenceMatcher

try:
    from .bk_tree import BKTree
    HAS_BKTREE = True
except ImportError:
    HAS_BKTREE = False


class SlugIndex:
    """Index of available article slugs from sitemap"""
    
    def __init__(self, links_dir: Optional[Path] = None, use_bktree: bool = True):
        """
        Initialize slug index.
        
        Args:
            links_dir: Path to links directory (default: auto-detect)
            use_bktree: Enable BK-Tree for O(log n) fuzzy search (default: True)
                       When enabled, provides 100-1000x speedup for fuzzy queries.
                       Adds ~5-10 seconds to initial load time for large datasets.
        """
        if links_dir is None:
            # Auto-detect links directory relative to this file
            sdk_dir = Path(__file__).parent
            links_dir = sdk_dir / "links"
        
        self.links_dir = Path(links_dir)
        self.use_bktree = use_bktree and HAS_BKTREE
        self._index: Optional[Dict[str, str]] = None
        self._all_slugs: Optional[List[str]] = None
        self._bk_tree: Optional['BKTree'] = None
    
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

    @staticmethod
    def _substring_match_score(text: str, pattern: str) -> Optional[Tuple[int, int, int]]:
        """Calculate a relevance score for substring matches.

        Scores favour exact matches, then word-boundary matches, prefixes, and finally
        loose substring matches. Returns None when pattern does not occur."""

        if not pattern:
            return None

        if text == pattern:
            return (4, 0, -len(text))

        best_score: Optional[Tuple[int, int, int]] = None
        start = 0

        while True:
            idx = text.find(pattern, start)
            if idx == -1:
                break

            before_char = text[idx - 1] if idx > 0 else ' '
            after_index = idx + len(pattern)
            after_char = text[after_index] if after_index < len(text) else ' '

            left_boundary = not before_char.isalnum()
            right_boundary = not after_char.isalnum()

            if left_boundary and right_boundary:
                primary = 3
            elif left_boundary or right_boundary:
                primary = 2
            else:
                primary = 1

            candidate_score = (primary, -idx, -len(text))
            if best_score is None or candidate_score > best_score:
                best_score = candidate_score

            # If we matched at the start with a word boundary on both sides, we won't
            # find a better occurrence for this string.
            if primary == 3 and idx == 0:
                break

            start = idx + 1

        return best_score

    @staticmethod
    def _compute_similarity_score(query: str, candidate: str) -> float:
        """Return a similarity score in the range [0, 100]."""

        if HAS_RAPIDFUZZ:
            if ' ' in query or ' ' in candidate:
                return float(max(
                    fuzz.token_set_ratio(query, candidate),
                    fuzz.WRatio(query, candidate),
                ))
            return float(fuzz.ratio(query, candidate))

        return SequenceMatcher(None, query, candidate).ratio() * 100.0

    def _collect_substring_candidates(
        self,
        index: Dict[str, str],
        query_normalized: str,
        limit: int,
    ) -> List[str]:
        """Gather top substring matches ranked by relevance."""

        candidate_scores: Dict[str, Tuple[int, int, int]] = {}

        for normalized_name, slug in index.items():
            if query_normalized not in normalized_name:
                continue

            score = self._substring_match_score(normalized_name, query_normalized)
            if score is None:
                continue

            existing = candidate_scores.get(slug)
            if existing is None or score > existing:
                candidate_scores[slug] = score

        if not candidate_scores:
            return []

        sorted_slugs = sorted(
            candidate_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return [slug for slug, _ in sorted_slugs[:limit]]
    
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
                except (IOError, OSError) as e:
                    # Handle file access errors (permissions, disk issues, etc.)
                    print(f"Warning: Could not read file {names_file}: {e}")
                    continue
                except UnicodeDecodeError as e:
                    # Handle encoding issues in the file
                    print(f"Warning: Could not decode {names_file} as UTF-8: {e}")
                    continue
        
        # Store sorted list of all unique slugs
        self._all_slugs = sorted(unique_slugs)
        
        # Build BK-Tree for O(log n) fuzzy search (if enabled)
        if self.use_bktree and HAS_BKTREE:
            self._bk_tree = BKTree()
            for slug in self._all_slugs:
                normalized = self._normalize_name(slug)
                self._bk_tree.add(slug, normalized)
        
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
        Search for matching slugs with optimized fuzzy matching.
        
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
            
        Note:
            - Uses BK-Tree for O(log n) fuzzy search when enabled (100-1000x faster)
            - Falls back to linear search with rapidfuzz if BK-Tree unavailable
            - Uses difflib.SequenceMatcher as final fallback
        """
        index = self.load()
        query_normalized = self._normalize_name(query)

        if limit <= 0:
            return []

        if not query_normalized:
            if not self._all_slugs:
                return []
            return self._all_slugs[:limit]

        # Strategy 1: Exact/substring matches ranked by relevance
        matches: List[str] = []
        seen = set()

        substring_candidates = self._collect_substring_candidates(index, query_normalized, limit)
        for slug in substring_candidates:
            if slug not in seen:
                matches.append(slug)
                seen.add(slug)
            if len(matches) >= limit:
                break

        if not fuzzy or len(matches) >= limit:
            return matches[:limit]
        
        # Strategy 2: Fuzzy matching if enabled and we don't have enough matches
        if fuzzy and len(matches) < limit:
            remaining = limit - len(matches)
            min_similarity_threshold = min_similarity * 100.0
            
            # Strategy 2a: Use BK-Tree for O(log n) fuzzy search (if available)
            if self._bk_tree is not None:
                # Convert similarity threshold to max edit distance
                query_len = len(query_normalized)
                max_distance = int(query_len * (1 - min_similarity))
                
                # Search BK-Tree (dramatically faster than linear scan)
                bk_results = self._bk_tree.search(query_normalized, max_distance, remaining * 5)

                ranked_candidates: List[Tuple[float, int, str]] = []

                for slug, distance in bk_results:
                    if slug in seen:
                        continue

                    candidate_normalized = self._normalize_name(slug)
                    similarity = self._compute_similarity_score(query_normalized, candidate_normalized)

                    if similarity < min_similarity_threshold:
                        continue

                    ranked_candidates.append((similarity, distance, slug))

                ranked_candidates.sort(key=lambda item: (-item[0], item[1], item[2]))

                for similarity, _, slug in ranked_candidates:
                    if slug not in seen:
                        matches.append(slug)
                        seen.add(slug)
                    if len(matches) >= limit:
                        break
            
            # Strategy 2b: Fallback to optimized linear search (if BK-Tree unavailable)
            else:
                # Use min-heap to efficiently track top-k results without sorting all items
                top_matches = []
                
                query_len = len(query_normalized)
                
                for normalized_name, slug in index.items():
                    if slug in seen:
                        continue  # Skip already matched slugs
                    
                    # Quick filter: skip if length difference is too large
                    name_len = len(normalized_name)
                    len_diff_ratio = abs(query_len - name_len) / max(query_len, name_len, 1)
                    
                    # Skip if length difference implies similarity below threshold
                    if len_diff_ratio > (1 - min_similarity):
                        continue
                    
                    # Calculate similarity ratio
                    similarity = self._compute_similarity_score(query_normalized, normalized_name)
                    
                    if similarity >= min_similarity_threshold:
                        if len(top_matches) < remaining:
                            heapq.heappush(top_matches, (similarity, -len(normalized_name), slug))
                        else:
                            smallest = top_matches[0]
                            if similarity > smallest[0]:
                                heapq.heapreplace(top_matches, (similarity, -len(normalized_name), slug))
                
                # Extract and sort matches from heap
                fuzzy_matches = sorted(top_matches, reverse=True)
                
                for _, _, slug in fuzzy_matches:
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
        self.load()
        
        if not self._all_slugs:
            return []
        
        # Don't try to sample more than available
        sample_size = min(count, len(self._all_slugs))
        return random.sample(self._all_slugs, sample_size)

