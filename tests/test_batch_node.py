import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pocketflow import BatchNode, Flow, Node


class ArrayChunkNode(BatchNode):
    def __init__(self, chunk_size=10):
        super().__init__()
        self.chunk_size = chunk_size
    
    def prep(self, shared):
        # Get array from shared storage and split into chunks
        array = shared.get('input_array', [])
        chunks = []
        for start in range(0, len(array), self.chunk_size):
            end = min(start + self.chunk_size, len(array))
            chunks.append(array[start: end])
        return chunks
    
    def exec(self, prep_res):
        # Process the chunk and return its sum
        chunk_sum = sum(prep_res)
        return chunk_sum
        
    def post(self, shared, prep_res, exec_res):
        # Store chunk results in shared storage
        shared['chunk_results'] = exec_res
        return "default"

class SumReduceNode(Node):
    def prep(self, shared):
        # Get chunk results from shared storage and sum them
        chunk_results = shared.get('chunk_results', [])
        total = sum(chunk_results)
        shared['total'] = total

class TestBatchNode(unittest.TestCase):
    def test_array_chunking(self):
        """
        Test that the array is correctly split into chunks
        """
        shared = {
            'input_array': list(range(25))  # [0,1,2,...,24]
        }
        
        chunk_node = ArrayChunkNode(chunk_size=10)
        chunk_node.run(shared)
        results = shared['chunk_results']
        self.assertEqual(results, [45, 145, 110])
        
    def test_map_reduce_sum(self):
        """
        Test a complete map-reduce pipeline that sums a large array:
        1. Map: Split array into chunks and sum each chunk
        2. Reduce: Sum all the chunk sums
        """
        # Create test array: [0,1,2,...,99]
        array = list(range(100))
        expected_sum = sum(array)  # 4950
        
        shared = {
            'input_array': array
        }
        
        # Create nodes
        chunk_node = ArrayChunkNode(chunk_size=10)
        reduce_node = SumReduceNode()
        
        # Connect nodes
        chunk_node >> reduce_node
        
        # Create and run pipeline
        pipeline = Flow(start=chunk_node)
        pipeline.run(shared)
        
        self.assertEqual(shared['total'], expected_sum)
        
    def test_uneven_chunks(self):
        """
        Test that the map-reduce works correctly with array lengths
        that don't divide evenly by chunk_size
        """
        array = list(range(25))
        expected_sum = sum(array)  # 300
        
        shared = {
            'input_array': array
        }
        
        chunk_node = ArrayChunkNode(chunk_size=10)
        reduce_node = SumReduceNode()
        
        chunk_node >> reduce_node
        pipeline = Flow(start=chunk_node)
        pipeline.run(shared)
        
        self.assertEqual(shared['total'], expected_sum)

    def test_custom_chunk_size(self):
        """
        Test that the map-reduce works with different chunk sizes
        """
        array = list(range(100))
        expected_sum = sum(array)
        
        shared = {
            'input_array': array
        }
        
        # Use chunk_size=15 instead of default 10
        chunk_node = ArrayChunkNode(chunk_size=15)
        reduce_node = SumReduceNode()
        
        chunk_node >> reduce_node
        pipeline = Flow(start=chunk_node)
        pipeline.run(shared)
        
        self.assertEqual(shared['total'], expected_sum)
        
    def test_single_element_chunks(self):
        """
        Test extreme case where chunk_size=1
        """
        array = list(range(5))
        expected_sum = sum(array)
        
        shared = {
            'input_array': array
        }
        
        chunk_node = ArrayChunkNode(chunk_size=1)
        reduce_node = SumReduceNode()
        
        chunk_node >> reduce_node
        pipeline = Flow(start=chunk_node)
        pipeline.run(shared)
        
        self.assertEqual(shared['total'], expected_sum)

    def test_empty_array(self):
        """
        Test edge case of empty input array
        """
        shared = {
            'input_array': []
        }
        
        chunk_node = ArrayChunkNode(chunk_size=10)
        reduce_node = SumReduceNode()
        
        chunk_node >> reduce_node
        pipeline = Flow(start=chunk_node)
        pipeline.run(shared)
        
        self.assertEqual(shared['total'], 0)

if __name__ == '__main__':
    unittest.main()
