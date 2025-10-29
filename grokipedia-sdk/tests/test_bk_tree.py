"""Tests for BKTree implementation"""

import pytest
from grokipedia_sdk.bk_tree import BKTree, BKTreeNode, build_bk_tree


class TestBKTreeNode:
    """Test BKTreeNode class"""
    
    def test_node_initialization(self):
        """Test BKTreeNode initialization"""
        node = BKTreeNode("Joe_Biden", "joe biden")
        
        assert node.slug == "Joe_Biden"
        assert node.normalized == "joe biden"
        assert isinstance(node.children, dict)
        assert len(node.children) == 0
    
    def test_node_children_dict(self):
        """Test that children is a dictionary"""
        node = BKTreeNode("Test", "test")
        
        # Can add children
        child_node = BKTreeNode("Child", "child")
        node.children[1] = child_node
        
        assert node.children[1] is child_node


class TestBKTreeInitialization:
    """Test BKTree initialization"""
    
    def test_tree_initialization(self):
        """Test empty BKTree initialization"""
        tree = BKTree()
        
        assert tree.root is None
        assert tree._size == 0
    
    def test_tree_empty_bool(self):
        """Test __bool__ for empty tree"""
        tree = BKTree()
        
        assert bool(tree) is False
    
    def test_tree_empty_len(self):
        """Test __len__ for empty tree"""
        tree = BKTree()
        
        assert len(tree) == 0


class TestBKTreeAdd:
    """Test BKTree.add() method"""
    
    def test_add_first_node(self):
        """Test adding first node becomes root"""
        tree = BKTree()
        tree.add("Joe_Biden", "joe biden")
        
        assert tree.root is not None
        assert tree.root.slug == "Joe_Biden"
        assert tree.root.normalized == "joe biden"
        assert len(tree) == 1
        assert bool(tree) is True
    
    def test_add_multiple_nodes(self):
        """Test adding multiple nodes"""
        tree = BKTree()
        tree.add("Joe_Biden", "joe biden")
        tree.add("Donald_Trump", "donald trump")
        tree.add("Barack_Obama", "barack obama")
        
        assert len(tree) == 3
    
    def test_add_same_distance_nodes(self):
        """Test adding nodes with same distance from root"""
        tree = BKTree()
        tree.add("cat", "cat")
        tree.add("dog", "dog")  # Both have distance 1 from each other
        
        assert len(tree) == 2
    
    def test_add_different_distance_nodes(self):
        """Test adding nodes with different distances"""
        tree = BKTree()
        tree.add("test", "test")
        tree.add("test2", "test2")  # Distance 1
        tree.add("testing", "testing")  # Distance 3
        
        assert len(tree) == 3


class TestBKTreeDistance:
    """Test BKTree._distance() method"""
    
    def test_distance_identical_strings(self):
        """Test distance for identical strings"""
        distance = BKTree._distance("test", "test")
        
        assert distance == 0
    
    def test_distance_different_strings(self):
        """Test distance for different strings"""
        distance = BKTree._distance("test", "best")
        
        assert distance > 0
        # Levenshtein distance: "test" -> "best" = 1 (replace 't' with 'b')
        assert distance == 1
    
    def test_distance_empty_strings(self):
        """Test distance with empty strings"""
        distance1 = BKTree._distance("", "")
        distance2 = BKTree._distance("test", "")
        distance3 = BKTree._distance("", "test")
        
        assert distance1 == 0
        assert distance2 == 4
        assert distance3 == 4
    
    def test_distance_unicode(self):
        """Test distance with unicode strings"""
        distance = BKTree._distance("café", "cafe")
        
        assert distance >= 0  # Should handle unicode


class TestBKTreeSearch:
    """Test BKTree.search() method"""
    
    def test_search_empty_tree(self):
        """Test searching empty tree returns empty list"""
        tree = BKTree()
        results = tree.search("test", max_distance=2)
        
        assert results == []
    
    def test_search_exact_match(self):
        """Test searching for exact match"""
        tree = BKTree()
        tree.add("Joe_Biden", "joe biden")
        
        results = tree.search("joe biden", max_distance=0)
        
        assert len(results) == 1
        assert results[0][0] == "Joe_Biden"
        assert results[0][1] == 0  # Exact match, distance 0
    
    def test_search_within_distance(self):
        """Test searching with distance threshold"""
        tree = BKTree()
        tree.add("Joe_Biden", "joe biden")
        
        results = tree.search("joe bidan", max_distance=1)  # Typo: bidan -> biden
        
        assert len(results) >= 1
        assert any(result[0] == "Joe_Biden" for result in results)
    
    def test_search_outside_distance(self):
        """Test searching with distance too small"""
        tree = BKTree()
        tree.add("Joe_Biden", "joe biden")
        
        results = tree.search("completely different", max_distance=2)
        
        # Should return empty if distance too large
        assert len(results) == 0 or all(result[1] > 2 for result in results)
    
    def test_search_limit(self):
        """Test that search respects limit parameter"""
        tree = BKTree()
        for i in range(10):
            tree.add(f"Article_{i}", f"article {i}")
        
        results = tree.search("article", max_distance=10, limit=5)
        
        assert len(results) <= 5
    
    def test_search_results_sorted_by_distance(self):
        """Test that search results are sorted by distance"""
        tree = BKTree()
        tree.add("test", "test")
        tree.add("testing", "testing")
        tree.add("tested", "tested")
        
        results = tree.search("test", max_distance=10)
        
        # Results should be sorted by distance (closest first)
        distances = [result[1] for result in results]
        assert distances == sorted(distances)
    
    def test_search_multiple_matches(self):
        """Test searching returns multiple matches"""
        tree = BKTree()
        tree.add("Joe_Biden", "joe biden")
        tree.add("Joe_Biden_Jr", "joe biden jr")
        tree.add("Joe_Biden_Sr", "joe biden sr")
        
        results = tree.search("joe biden", max_distance=5)
        
        assert len(results) >= 2
    
    def test_search_case_sensitive(self):
        """Test that search is case-sensitive by default"""
        tree = BKTree()
        tree.add("Test", "test")
        
        # Case mismatch should have distance > 0
        results = tree.search("TEST", max_distance=0)
        
        # Should not find exact match (case different)
        exact_matches = [r for r in results if r[1] == 0]
        assert len(exact_matches) == 0


class TestBKTreeRecursiveSearch:
    """Test BKTree._search_recursive() method"""
    
    def test_recursive_search_finds_all_matches(self):
        """Test recursive search finds all matches in tree"""
        tree = BKTree()
        tree.add("test", "test")
        tree.add("testing", "testing")
        tree.add("tested", "tested")
        tree.add("best", "best")
        
        results = []
        tree._search_recursive(tree.root, "test", max_distance=10, results=results, limit=10)
        
        assert len(results) >= 1
    
    def test_recursive_search_respects_limit(self):
        """Test that search() respects limit (limit is enforced in search method)"""
        tree = BKTree()
        for i in range(5):
            tree.add(f"test{i}", f"test{i}")
        
        # Use search() method which properly enforces limit
        results = tree.search("test", max_distance=10, limit=2)
        
        assert len(results) <= 2


class TestBKTreeBuildHelper:
    """Test build_bk_tree() helper function"""
    
    def test_build_bk_tree_basic(self):
        """Test building BKTree from list"""
        slugs = ["Joe_Biden", "Donald_Trump", "Barack_Obama"]
        
        def normalize(slug):
            return slug.lower().replace('_', ' ')
        
        tree = build_bk_tree(slugs, normalize)
        
        assert len(tree) == 3
        assert bool(tree) is True
    
    def test_build_bk_tree_empty_list(self):
        """Test building BKTree from empty list"""
        def normalize(slug):
            return slug.lower()
        
        tree = build_bk_tree([], normalize)
        
        assert len(tree) == 0
        assert bool(tree) is False
    
    def test_build_bk_tree_searchable(self):
        """Test that built tree is searchable"""
        slugs = ["Joe_Biden", "Donald_Trump"]
        
        def normalize(slug):
            return slug.lower().replace('_', ' ')
        
        tree = build_bk_tree(slugs, normalize)
        
        results = tree.search("joe bidan", max_distance=2)
        assert len(results) >= 1


class TestBKTreeEdgeCases:
    """Test BKTree edge cases"""
    
    def test_tree_with_single_node(self):
        """Test tree with single node"""
        tree = BKTree()
        tree.add("test", "test")
        
        assert len(tree) == 1
        assert tree.root.slug == "test"
        
        results = tree.search("test", max_distance=0)
        assert len(results) == 1
    
    def test_tree_with_duplicate_normalized(self):
        """Test tree with duplicate normalized strings"""
        tree = BKTree()
        tree.add("Test", "test")
        tree.add("TEST", "test")  # Same normalized
        
        assert len(tree) == 2
    
    def test_tree_with_very_long_strings(self):
        """Test tree with very long strings"""
        tree = BKTree()
        long_string = "A" * 1000
        tree.add("Long", long_string)
        
        assert len(tree) == 1
        results = tree.search(long_string, max_distance=0)
        assert len(results) == 1
    
    def test_tree_with_special_characters(self):
        """Test tree with special characters"""
        tree = BKTree()
        tree.add("Test_Article", "test article")
        tree.add("Test@Article", "test@article")
        
        assert len(tree) == 2
    
    def test_tree_with_unicode(self):
        """Test tree with unicode characters"""
        tree = BKTree()
        tree.add("北京", "北京")
        tree.add("François", "françois")
        
        assert len(tree) == 2
        
        results = tree.search("北京", max_distance=0)
        assert len(results) == 1
    
    def test_tree_max_distance_zero(self):
        """Test search with max_distance=0 (exact match only)"""
        tree = BKTree()
        tree.add("test", "test")
        tree.add("testing", "testing")
        
        results = tree.search("test", max_distance=0)
        
        # Should only find exact matches
        assert all(result[1] == 0 for result in results)
    
    def test_tree_max_distance_large(self):
        """Test search with very large max_distance"""
        tree = BKTree()
        tree.add("test", "test")
        tree.add("testing", "testing")
        tree.add("completely", "completely")
        
        results = tree.search("test", max_distance=100)
        
        # Should find all matches
        assert len(results) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

