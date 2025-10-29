"""
BK-Tree (Burkhard-Keller Tree) implementation for fast fuzzy string search.

A BK-Tree is a metric tree data structure optimized for approximate string matching.
It allows searching for strings within a given edit distance in O(log n) time,
compared to O(n) for linear search.

References:
    - Burkhard, W. A.; Keller, R. M. (1973). "Some approaches to best-match file searching"
    - https://en.wikipedia.org/wiki/BK-tree
"""

from typing import List, Tuple, Optional, Dict

try:
    from rapidfuzz.distance import Levenshtein
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


class BKTreeNode:
    """
    Node in a BK-Tree.
    
    Each node stores a string and has children at distances determined by
    the edit distance metric.
    """
    
    __slots__ = ['slug', 'normalized', 'children']
    
    def __init__(self, slug: str, normalized: str):
        """
        Initialize a BK-Tree node.
        
        Args:
            slug: Original slug (e.g., "Joe_Biden")
            normalized: Normalized version for matching (e.g., "joe biden")
        """
        self.slug = slug
        self.normalized = normalized
        self.children: Dict[int, BKTreeNode] = {}


class BKTree:
    """
    BK-Tree for fast approximate string matching.
    
    A BK-Tree organizes strings based on their edit distances, allowing
    efficient fuzzy search queries. Instead of comparing against all strings
    in the dataset, the tree structure prunes large portions of the search space.
    
    Time Complexity:
        - Build: O(n log n) where n is number of strings
        - Search: O(log n) on average (vs O(n) for linear search)
        - Space: O(n) with ~2-3x overhead for tree structure
    
    Example:
        >>> tree = BKTree()
        >>> tree.add("Joe_Biden", "joe biden")
        >>> tree.add("Joe_Biden_Jr", "joe biden jr")
        >>> results = tree.search("joe bidan", max_distance=2, limit=5)
        >>> # Returns slugs within 2 edits: [("Joe_Biden", 1), ...]
    """
    
    def __init__(self):
        """Initialize an empty BK-Tree."""
        self.root: Optional[BKTreeNode] = None
        self._size = 0
    
    def add(self, slug: str, normalized: str) -> None:
        """
        Add a string to the BK-Tree.
        
        Args:
            slug: Original slug to store
            normalized: Normalized version used for distance calculations
            
        Example:
            >>> tree = BKTree()
            >>> tree.add("Joe_Biden", "joe biden")
        """
        if self.root is None:
            self.root = BKTreeNode(slug, normalized)
            self._size = 1
            return
        
        current = self.root
        distance = self._distance(normalized, current.normalized)
        
        # Traverse tree to find insertion point
        while distance in current.children:
            current = current.children[distance]
            distance = self._distance(normalized, current.normalized)
        
        # Insert new node
        current.children[distance] = BKTreeNode(slug, normalized)
        self._size += 1
    
    def search(
        self,
        query: str,
        max_distance: int,
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Search for strings within a given edit distance.
        
        Args:
            query: Query string (normalized)
            max_distance: Maximum edit distance (0 = exact match, higher = more fuzzy)
            limit: Maximum number of results to return
            
        Returns:
            List of (slug, distance) tuples, sorted by distance (closest first)
            
        Example:
            >>> tree = BKTree()
            >>> tree.add("Joe_Biden", "joe biden")
            >>> tree.search("joe bidan", max_distance=2)
            [('Joe_Biden', 1)]
            
        Note:
            For similarity threshold (0.0-1.0), convert to edit distance:
            max_distance = int(len(query) * (1 - min_similarity))
        """
        if self.root is None:
            return []
        
        results: List[Tuple[str, int]] = []
        self._search_recursive(self.root, query, max_distance, results, limit)
        
        # Sort by distance (closest first), then by slug name
        results.sort(key=lambda x: (x[1], x[0]))
        return results[:limit]
    
    def _search_recursive(
        self,
        node: BKTreeNode,
        query: str,
        max_distance: int,
        results: List[Tuple[str, int]],
        limit: int
    ) -> None:
        """
        Recursively search the BK-Tree.
        
        The key insight: if a node is at distance d from the query, then
        all candidate matches must be in children at distances in the range
        [d - max_distance, d + max_distance]. This prunes most of the tree.
        
        Args:
            node: Current node being examined
            query: Query string
            max_distance: Maximum edit distance threshold
            results: Accumulator for matching results
            limit: Stop early if we have enough results
        """
        # Calculate distance from query to current node
        distance = self._distance(query, node.normalized)
        
        # If within threshold, add to results
        if distance <= max_distance:
            results.append((node.slug, distance))
            
            # Early termination if we have enough exact matches
            if distance == 0 and len(results) >= limit:
                return
        
        # Search children in the relevant distance range
        # This is the key optimization: we only explore children where
        # candidates could possibly exist
        min_child_dist = max(0, distance - max_distance)
        max_child_dist = distance + max_distance
        
        # Early termination optimization: if we have enough results, only continue
        # if we might find better matches than what we already have
        if len(results) >= limit:
            # Find the worst (highest) distance in current results
            current_worst_distance = max(results, key=lambda x: x[1])[1] if results else max_distance
            # Prune this branch if even the best possible match would be worse
            # The triangle inequality tells us that exploring children can't give us
            # matches better than (distance - max_distance) at best
            if distance > current_worst_distance + max_distance:
                return  # Prune this branch - can't find better matches
        
        for child_dist in range(min_child_dist, max_child_dist + 1):
            if child_dist in node.children:
                self._search_recursive(
                    node.children[child_dist],
                    query,
                    max_distance,
                    results,
                    limit
                )
    
    @staticmethod
    def _distance(s1: str, s2: str) -> int:
        """
        Calculate edit distance between two strings.
        
        Uses Levenshtein distance (minimum number of single-character edits
        required to change one string into another).
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Edit distance (0 = identical, higher = more different)
            
        Note:
            Uses rapidfuzz.distance.Levenshtein if available (fast C implementation),
            otherwise falls back to pure Python implementation (Wagner-Fischer algorithm).
        """
        if HAS_RAPIDFUZZ:
            # Fast C implementation
            return Levenshtein.distance(s1, s2)
        else:
            # Pure Python Levenshtein distance (Wagner-Fischer algorithm)
            # This ensures consistent behavior regardless of rapidfuzz availability
            if s1 == s2:
                return 0
            if len(s1) == 0:
                return len(s2)
            if len(s2) == 0:
                return len(s1)
            
            # Create distance matrix
            # Optimized to use only two rows instead of full matrix
            len1, len2 = len(s1), len(s2)
            prev_row = list(range(len2 + 1))
            curr_row = [0] * (len2 + 1)
            
            for i in range(len1):
                curr_row[0] = i + 1
                for j in range(len2):
                    # Cost of substitution (0 if characters match, 1 otherwise)
                    cost = 0 if s1[i] == s2[j] else 1
                    curr_row[j + 1] = min(
                        prev_row[j + 1] + 1,    # deletion
                        curr_row[j] + 1,        # insertion
                        prev_row[j] + cost      # substitution
                    )
                # Swap rows for next iteration
                prev_row, curr_row = curr_row, prev_row
            
            return prev_row[len2]
    
    def __len__(self) -> int:
        """Return the number of strings in the tree."""
        return self._size
    
    def __bool__(self) -> bool:
        """Return True if tree is not empty."""
        return self.root is not None


def build_bk_tree(slugs: List[str], normalize_fn) -> BKTree:
    """
    Build a BK-Tree from a list of slugs.
    
    Convenience function for batch construction.
    
    Args:
        slugs: List of article slugs
        normalize_fn: Function to normalize slugs (e.g., lowercase, remove underscores)
        
    Returns:
        Populated BK-Tree ready for searching
        
    Example:
        >>> def normalize(s):
        ...     return s.lower().replace('_', ' ')
        >>> slugs = ["Joe_Biden", "Donald_Trump", "Barack_Obama"]
        >>> tree = build_bk_tree(slugs, normalize)
        >>> results = tree.search("joe bidan", max_distance=2)
    """
    tree = BKTree()
    for slug in slugs:
        normalized = normalize_fn(slug)
        tree.add(slug, normalized)
    return tree

