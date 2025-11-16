
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False
        self.word = None


class TrieMap:
    def __init__(self):
        self.root = TrieNode()
        self.size = 0
    
    def insert(self, word: str) -> None:
        if not word:
            return
        
        word = word.lower().strip()
        node = self.root
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        if not node.is_word:
            node.is_word = True
            node.word = word
            self.size += 1
    
    def search(self, word: str) -> bool:
        node = self._find_node(word)
        return node is not None and node.is_word
    
    def starts_with(self, prefix: str) -> bool:
        node = self._find_node(prefix)
        return node is not None
    
    def _find_node(self, prefix: str) -> TrieNode:
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node
    
    def load_from_file(self, filepath: str, min_length: int = 3) -> None:
        with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('"') and '":' in line:
                        word = line.split('":')[0].strip('"').lower()
                    else:
                        word = line.lower()
                    if len(word) >= min_length and word.isalpha():
                        self.insert(word)
    
    def load_from_list(self, words: list, min_length: int = 3) -> None:
        for word in words:
            word_str = str(word).strip().lower()
            if len(word_str) >= min_length and word_str.isalpha():
                self.insert(word_str)

