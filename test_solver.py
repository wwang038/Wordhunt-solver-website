import unittest
from trie import TrieMap
from board import Board
from solver import Solver, load_dictionary


class TestSolver(unittest.TestCase):
    
    def setUp(self):
        self.dictionary = TrieMap()
        test_words = [
            "cat", "dog", "bat", "rat", "mat", "hat", "pat", "sat", "fat", "vat",
            "cafe", "game", "fame", "lame", "name", "same", "tame", "came",
            "flame", "frame", "shame", "blame",
            "acted", "faced", "raced",
            "flaming", "framing"
        ]
        self.dictionary.load_from_list(test_words, min_length=3)
        self.solver = Solver(self.dictionary)
    
    def test_init(self):
        solver = Solver(self.dictionary)
        self.assertIsInstance(solver.dictionary, TrieMap)
        self.assertEqual(len(solver.found_words), 0)
        self.assertEqual(solver.found_words, set())
    
    def test_calculate_score_3_letters(self):
        self.assertEqual(self.solver._calculate_score("cat"), 100)
        self.assertEqual(self.solver._calculate_score("dog"), 100)
        self.assertEqual(self.solver._calculate_score("bat"), 100)
    
    def test_calculate_score_4_letters(self):
        self.assertEqual(self.solver._calculate_score("cafe"), 400)
        self.assertEqual(self.solver._calculate_score("game"), 400)
        self.assertEqual(self.solver._calculate_score("fame"), 400)
    
    def test_calculate_score_5_letters(self):
        self.assertEqual(self.solver._calculate_score("flame"), 800)
        self.assertEqual(self.solver._calculate_score("frame"), 800)
        self.assertEqual(self.solver._calculate_score("shame"), 800)
    
    def test_calculate_score_6_letters(self):
        self.assertEqual(self.solver._calculate_score("abcdef"), 1400)
        self.assertEqual(self.solver._calculate_score("tested"), 1400)
    
    def test_calculate_score_7_letters(self):
        self.assertEqual(self.solver._calculate_score("testing"), 1800)
    
    def test_calculate_score_8_plus_letters(self):
        self.assertEqual(self.solver._calculate_score("abcdefgh"), 2200)
        self.assertEqual(self.solver._calculate_score("abcdefghi"), 2600)
        self.assertEqual(self.solver._calculate_score("verylongword"), 3800)
    
    def test_calculate_score_short_words(self):
        self.assertEqual(self.solver._calculate_score("a"), -600)
        self.assertEqual(self.solver._calculate_score("ab"), -200)
        self.assertEqual(self.solver._calculate_score(""), -1000)
    
    def test_solve_simple_board(self):
        board = Board("catdogxxy")
        results = self.solver.solve(board)
        
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        
        found_words = [word for word, _ in results]
        self.assertIn("cat", found_words)
        self.assertIn("dog", found_words)
    
    def test_solve_finds_single_word(self):
        board = Board("catxxxxxx")
        results = self.solver.solve(board)
        
        found_words = [word for word, _ in results]
        self.assertIn("cat", found_words)
    
    def test_solve_results_sorted_by_score(self):
        board = Board("catdogefghijklmn")
        results = self.solver.solve(board)
        
        if len(results) >= 2:
            for i in range(len(results) - 1):
                score1 = results[i][1]
                score2 = results[i + 1][1]
                self.assertGreaterEqual(score1, score2)
    
    def test_solve_results_sorted_lexicographically_same_score(self):
        board = Board("catdogefghijklmn")
        results = self.solver.solve(board)
        
        grouped = {}
        for word, score in results:
            if score not in grouped:
                grouped[score] = []
            grouped[score].append(word)
        
        for score, words in grouped.items():
            if len(words) > 1:
                sorted_words = sorted(words)
                self.assertEqual(words, sorted_words)
    
    def test_solve_no_valid_words(self):
        empty_dict = TrieMap()
        solver = Solver(empty_dict)
        board = Board("abcdefghijklmnop")
        results = solver.solve(board)
        
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])
    
    def test_solve_clears_previous_results(self):
        board1 = Board("catxxxxxx")
        results1 = self.solver.solve(board1)
        
        board2 = Board("dogxxxxxx")
        results2 = self.solver.solve(board2)
        
        found_words1 = [word for word, _ in results1]
        found_words2 = [word for word, _ in results2]
        
        self.assertIn("cat", found_words1)
        self.assertNotIn("cat", found_words2)
        self.assertIn("dog", found_words2)
    
    def test_solve_4x4_board(self):
        board = Board("catefghijklmnopr")
        results = self.solver.solve(board)
        
        self.assertIsInstance(results, list)
        
        found_words = [word for word, _ in results]
        self.assertIn("cat", found_words)
    
    def test_solve_all_positions_visited(self):
        board = Board("catxxxxxx")
        results = self.solver.solve(board)
        
        self.assertGreaterEqual(len(results), 1)
        found_words = [word for word, _ in results]
        self.assertIn("cat", found_words)
    
    def test_solve_minimum_word_length(self):
        short_dict = TrieMap()
        short_dict.insert("ab")
        short_dict.insert("abc")
        short_dict.insert("abcd")
        
        solver = Solver(short_dict)
        board = Board("abcxxxxxx")
        results = solver.solve(board)
        
        found_words = [word for word, _ in results]
        self.assertNotIn("ab", found_words)
        self.assertIn("abc", found_words)
    
    def test_solve_duplicate_words_removed(self):
        board = Board("catxxxxxx")
        results = self.solver.solve(board)
        
        found_words = [word for word, _ in results]
        unique_words = set(found_words)
        self.assertEqual(len(found_words), len(unique_words))
    
    def test_solve_word_scores_correct(self):
        board = Board("catxxxxxx")
        results = self.solver.solve(board)
        
        for word, score in results:
            expected_score = self.solver._calculate_score(word)
            self.assertEqual(score, expected_score)
    
    def test_solve_repeated_letters(self):
        board = Board("aaaaaaaaaaaaaaaa")
        results = self.solver.solve(board)
        
        self.assertIsInstance(results, list)
    
    def test_solve_complex_path(self):
        board = Board("catxxxxxx")
        results = self.solver.solve(board)
        
        found_words = [word for word, _ in results]
        self.assertIn("cat", found_words)
    
    def test_solve_adjacent_cells_only(self):
        board = Board("catdogefghijklmn")
        results = self.solver.solve(board)
        
        found_words = [word for word, _ in results]
        for word in found_words:
            self.assertTrue(len(word) >= 3)


class TestSolverIntegration(unittest.TestCase):
    
    def test_full_workflow(self):
        dictionary = TrieMap()
        dictionary.load_from_list(["cat", "dog", "bat", "rat"], min_length=3)
        
        board = Board("catxxxxxx")
        solver = Solver(dictionary)
        results = solver.solve(board)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        found_words = [word for word, _ in results]
        self.assertIn("cat", found_words)
        
        for word, score in results:
            self.assertIsInstance(word, str)
            self.assertIsInstance(score, int)
            self.assertGreaterEqual(score, 0)
            self.assertGreaterEqual(len(word), 3)
    
    def test_solve_with_specific_board(self):
        dictionary = TrieMap()
        words = ["cat", "dog", "act", "god"]
        dictionary.load_from_list(words, min_length=3)
        
        board = Board("catxxxxxx")
        solver = Solver(dictionary)
        results = solver.solve(board)
        
        found_words = [word for word, _ in results]
        
        self.assertIn("cat", found_words)
        self.assertGreater(len(results), 0)
    
    def test_solve_multiple_runs(self):
        dictionary = TrieMap()
        dictionary.load_from_list(["cat", "dog"], min_length=3)
        
        solver = Solver(dictionary)
        
        board1 = Board("catxxxxxx")
        results1 = solver.solve(board1)
        
        board2 = Board("dogxxxxxx")
        results2 = solver.solve(board2)
        
        found_words1 = [word for word, _ in results1]
        found_words2 = [word for word, _ in results2]
        
        self.assertIn("cat", found_words1)
        self.assertNotIn("cat", found_words2)
        self.assertIn("dog", found_words2)
        self.assertNotIn("dog", found_words1)
    
    def test_solve_results_format(self):
        dictionary = TrieMap()
        dictionary.load_from_list(["cat", "dog"], min_length=3)
        
        board = Board("catdogefghijklmn")
        solver = Solver(dictionary)
        results = solver.solve(board)
        
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            word, score = result
            self.assertIsInstance(word, str)
            self.assertIsInstance(score, int)


class TestLoadDictionary(unittest.TestCase):
    
    def test_load_dictionary_custom_path(self):
        dictionary = load_dictionary("words_alpha.txt")
        self.assertIsInstance(dictionary, TrieMap)
        self.assertGreater(dictionary.size, 0)
    
    def test_load_dictionary_default(self):
        dictionary = load_dictionary()
        self.assertIsInstance(dictionary, TrieMap)
        self.assertGreater(dictionary.size, 0)
    
    def test_load_dictionary_none(self):
        dictionary = load_dictionary(None)
        self.assertIsInstance(dictionary, TrieMap)
        self.assertGreater(dictionary.size, 0)


if __name__ == '__main__':
    unittest.main()
