import unittest
import tempfile
from backend.trie import TrieNode, TrieMap


class TestTrieNode(unittest.TestCase):
    
    def test_init(self):
        node = TrieNode()
        self.assertEqual(node.children, {})
        self.assertFalse(node.is_word)
        self.assertIsNone(node.word)
    
    def test_node_properties(self):
        node = TrieNode()
        node.is_word = True
        node.word = "test"
        node.children['a'] = TrieNode()
        
        self.assertTrue(node.is_word)
        self.assertEqual(node.word, "test")
        self.assertIn('a', node.children)
        self.assertIsInstance(node.children['a'], TrieNode)


class TestTrieMap(unittest.TestCase):
    
    def setUp(self):
        self.trie = TrieMap()
    
    def test_init(self):
        self.assertIsInstance(self.trie.root, TrieNode)
        self.assertEqual(self.trie.size, 0)
    
    def test_insert_single_word(self):
        self.trie.insert("cat")
        self.assertEqual(self.trie.size, 1)
        self.assertTrue(self.trie.search("cat"))
    
    def test_insert_multiple_words(self):
        words = ["cat", "dog", "bat"]
        for word in words:
            self.trie.insert(word)
        
        self.assertEqual(self.trie.size, 3)
        for word in words:
            self.assertTrue(self.trie.search(word))
    
    def test_insert_duplicate_word(self):
        self.trie.insert("cat")
        self.assertEqual(self.trie.size, 1)
        
        self.trie.insert("cat")
        self.assertEqual(self.trie.size, 1)
    
    def test_insert_empty_string(self):
        self.trie.insert("")
        self.assertEqual(self.trie.size, 0)
        self.assertFalse(self.trie.search(""))
    
    def test_insert_case_insensitive(self):
        self.trie.insert("Cat")
        self.trie.insert("DOG")
        self.trie.insert("BaT")
        
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("bat"))
        self.assertEqual(self.trie.size, 3)
        
        self.assertFalse(self.trie.search("CAT"))
        self.assertFalse(self.trie.search("DOG"))
    
    def test_insert_with_whitespace(self):
        self.trie.insert("  cat  ")
        self.trie.insert("dog\n")
        self.trie.insert("\tbat\t")
        
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("bat"))
        self.assertEqual(self.trie.size, 3)
    
    def test_search_existing_word(self):
        self.trie.insert("cat")
        self.trie.insert("dog")
        self.trie.insert("catalog")
        
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("catalog"))
    
    def test_search_nonexistent_word(self):
        self.trie.insert("cat")
        
        self.assertFalse(self.trie.search("dog"))
        self.assertFalse(self.trie.search("ca"))
        self.assertFalse(self.trie.search("catt"))
        self.assertFalse(self.trie.search(""))
    
    def test_search_partial_match(self):
        self.trie.insert("catalog")
        
        self.assertFalse(self.trie.search("cat"))
        self.assertFalse(self.trie.search("cata"))
        self.assertTrue(self.trie.search("catalog"))
    
    def test_starts_with_existing_prefix(self):
        self.trie.insert("cat")
        self.trie.insert("catalog")
        self.trie.insert("category")
        
        self.assertTrue(self.trie.starts_with("c"))
        self.assertTrue(self.trie.starts_with("ca"))
        self.assertTrue(self.trie.starts_with("cat"))
        self.assertTrue(self.trie.starts_with("cata"))
        self.assertTrue(self.trie.starts_with("catalog"))
    
    def test_starts_with_nonexistent_prefix(self):
        self.trie.insert("cat")
        
        self.assertFalse(self.trie.starts_with("d"))
        self.assertFalse(self.trie.starts_with("caa"))
        self.assertFalse(self.trie.starts_with("catt"))
    
    def test_starts_with_empty_string(self):
        self.trie.insert("cat")
        
        self.assertTrue(self.trie.starts_with(""))
    
    def test_find_node_existing(self):
        self.trie.insert("cat")
        self.trie.insert("dog")
        
        node = self.trie._find_node("cat")
        self.assertIsNotNone(node)
        self.assertTrue(node.is_word)
        self.assertEqual(node.word, "cat")
        
        node = self.trie._find_node("ca")
        self.assertIsNotNone(node)
        self.assertFalse(node.is_word)
    
    def test_find_node_nonexistent(self):
        self.trie.insert("cat")
        
        self.assertIsNone(self.trie._find_node("dog"))
        self.assertIsNone(self.trie._find_node("catt"))
        self.assertIsNone(self.trie._find_node("caa"))
    
    def test_load_from_list_basic(self):
        words = ["cat", "dog", "bat", "rat"]
        self.trie.load_from_list(words)
        
        self.assertEqual(self.trie.size, 4)
        for word in words:
            self.assertTrue(self.trie.search(word))
    
    def test_load_from_list_with_min_length(self):
        words = ["a", "ab", "abc", "abcd", "abcde"]
        self.trie.load_from_list(words, min_length=3)
        
        self.assertFalse(self.trie.search("a"))
        self.assertFalse(self.trie.search("ab"))
        self.assertTrue(self.trie.search("abc"))
        self.assertTrue(self.trie.search("abcd"))
        self.assertTrue(self.trie.search("abcde"))
        self.assertEqual(self.trie.size, 3)
    
    def test_load_from_list_filters_non_alpha(self):
        words = ["cat", "dog123", "bat!", "rat", "word-with-dash"]
        self.trie.load_from_list(words)
        
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("rat"))
        self.assertFalse(self.trie.search("dog123"))
        self.assertFalse(self.trie.search("bat!"))
        self.assertFalse(self.trie.search("word-with-dash"))
        self.assertEqual(self.trie.size, 2)
    
    def test_load_from_list_case_handling(self):
        words = ["Cat", "DOG", "BaT"]
        self.trie.load_from_list(words)
        
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("bat"))
        self.assertEqual(self.trie.size, 3)
    
    def test_load_from_file_plain_format(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("cat\ndog\nbat\nrat\n")
            temp_path = f.name
        
        self.trie.load_from_file(temp_path)
        self.assertEqual(self.trie.size, 4)
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("bat"))
        self.assertTrue(self.trie.search("rat"))
    
    def test_load_from_file_json_format(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write('"cat": 1,\n"dog": 1,\n"bat": 1,\n')
            temp_path = f.name
        
        self.trie.load_from_file(temp_path)
        self.assertEqual(self.trie.size, 3)
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("bat"))
    
    def test_load_from_file_mixed_format(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write('"cat": 1,\ndog\n"bat": 1,\nrat\n')
            temp_path = f.name
        
        self.trie.load_from_file(temp_path)
        self.assertEqual(self.trie.size, 4)
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("bat"))
        self.assertTrue(self.trie.search("rat"))
    
    def test_load_from_file_with_min_length(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("a\nab\nabc\nabcd\n")
            temp_path = f.name
        
        self.trie.load_from_file(temp_path, min_length=3)
        self.assertEqual(self.trie.size, 2)
        self.assertFalse(self.trie.search("a"))
        self.assertFalse(self.trie.search("ab"))
        self.assertTrue(self.trie.search("abc"))
        self.assertTrue(self.trie.search("abcd"))
    
    def test_load_from_file_filters_non_alpha(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("cat\ndog123\nbat!\nrat\n")
            temp_path = f.name
        
        self.trie.load_from_file(temp_path)
        self.assertEqual(self.trie.size, 2)
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("rat"))
        self.assertFalse(self.trie.search("dog123"))
        self.assertFalse(self.trie.search("bat!"))
    
    def test_load_from_file_skips_empty_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("cat\n\n\ndog\n\nbat\n")
            temp_path = f.name
        
        self.trie.load_from_file(temp_path)
        self.assertEqual(self.trie.size, 3)
        self.assertTrue(self.trie.search("cat"))
        self.assertTrue(self.trie.search("dog"))
        self.assertTrue(self.trie.search("bat"))
    
    def test_complex_word_relationships(self):
        words = ["cat", "catalog", "category", "dog", "dogma"]
        self.trie.load_from_list(words)
        
        for word in words:
            self.assertTrue(self.trie.search(word))
        
        self.assertTrue(self.trie.starts_with("cat"))
        self.assertTrue(self.trie.starts_with("cata"))
        self.assertTrue(self.trie.starts_with("categor"))
        
        self.assertTrue(self.trie.starts_with("dog"))
        self.assertTrue(self.trie.starts_with("dogm"))
        
        self.assertFalse(self.trie.search("cata"))
        self.assertFalse(self.trie.search("categor"))
        self.assertFalse(self.trie.search("dogm"))
    
    def test_large_word_list(self):
        words = []
        for i in range(1000):
            suffix = ""
            num = i
            while num >= 0:
                suffix = chr(97 + (num % 26)) + suffix
                num = num // 26 - 1
            words.append(f"word{suffix}")
        
        self.trie.load_from_list(words)
        
        self.assertEqual(self.trie.size, 1000)
        self.assertTrue(self.trie.search("worda"))
        self.assertTrue(self.trie.search("wordz"))
        self.assertTrue(self.trie.search(words[500]))
        self.assertFalse(self.trie.search("wordzzzz"))


class TestTrieMapIntegration(unittest.TestCase):
    
    def test_full_workflow(self):
        trie = TrieMap()
        
        words = ["cat", "dog", "bat", "rat", "catalog", "category"]
        for word in words:
            trie.insert(word)
        
        self.assertEqual(trie.size, 6)
        for word in words:
            self.assertTrue(trie.search(word))
        
        self.assertTrue(trie.starts_with("cat"))
        self.assertTrue(trie.starts_with("cata"))
        self.assertTrue(trie.starts_with("categor"))
        
        self.assertFalse(trie.search("mouse"))
        self.assertFalse(trie.search("catt"))
        self.assertFalse(trie.starts_with("xyz"))


if __name__ == '__main__':
    unittest.main()

