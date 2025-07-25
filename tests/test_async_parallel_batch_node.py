import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pocketflow import AsyncParallelBatchNode


class AsyncParallelNumberProcessor(AsyncParallelBatchNode):
    def __init__(self, delay=0.1):
        super().__init__()
        self.delay = delay
    
    async def prep_async(self, shared):
        numbers = shared.get('input_numbers', [])
        return numbers
    
    async def exec_async(self, prep_res):
        await asyncio.sleep(self.delay)  # Simulate async processing
        return prep_res * 2
        
    async def post_async(self, shared, prep_res, exec_res):
        shared['processed_numbers'] = exec_res
        return "processed"

class TestAsyncParallelBatchNode(unittest.TestCase):
    def setUp(self):
        # Reset the event loop for each test
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_parallel_processing(self):
        """
        Test that numbers are processed in parallel by measuring execution time
        """
        shared = {
            'input_numbers': list(range(5))
        }
        
        processor = AsyncParallelNumberProcessor(delay=0.1)
        
        # Run the processor
        start_time = asyncio.get_event_loop().time()
        self.loop.run_until_complete(processor.run_async(shared))
        end_time = asyncio.get_event_loop().time()
        
        # Check results
        expected = [0, 2, 4, 6, 8]  # Each number doubled
        self.assertEqual(shared['processed_numbers'], expected)
        
        # Since processing is parallel, total time should be approximately
        # equal to the delay of a single operation, not delay * number_of_items
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.2)  # Should be around 0.1s plus minimal overhead
    
    def test_empty_input(self):
        """
        Test processing of empty input
        """
        shared = {
            'input_numbers': []
        }
        
        processor = AsyncParallelNumberProcessor()
        self.loop.run_until_complete(processor.run_async(shared))
        
        self.assertEqual(shared['processed_numbers'], [])
    
    def test_single_item(self):
        """
        Test processing of a single item
        """
        shared = {
            'input_numbers': [42]
        }
        
        processor = AsyncParallelNumberProcessor()
        self.loop.run_until_complete(processor.run_async(shared))
        
        self.assertEqual(shared['processed_numbers'], [84])
    
    def test_large_batch(self):
        """
        Test processing of a large batch of numbers
        """
        input_size = 100
        shared = {
            'input_numbers': list(range(input_size))
        }
        
        processor = AsyncParallelNumberProcessor(delay=0.01)
        self.loop.run_until_complete(processor.run_async(shared))
        
        expected = [x * 2 for x in range(input_size)]
        self.assertEqual(shared['processed_numbers'], expected)
    
    def test_error_handling(self):
        """
        Test error handling during parallel processing
        """
        class ErrorProcessor(AsyncParallelNumberProcessor):
            async def exec_async(self, prep_res):
                if prep_res == 2:
                    raise ValueError(f"Error processing item {prep_res}")
                return prep_res
        
        shared = {
            'input_numbers': [1, 2, 3]
        }
        
        processor = ErrorProcessor()
        with self.assertRaises(ValueError):
            self.loop.run_until_complete(processor.run_async(shared))
    
    def test_concurrent_execution(self):
        """
        Test that tasks are actually running concurrently by tracking execution order
        """
        execution_order = []
        
        class OrderTrackingProcessor(AsyncParallelNumberProcessor):
            async def exec_async(self, prep_res):
                delay = 0.1 if prep_res % 2 == 0 else 0.05
                await asyncio.sleep(delay)
                execution_order.append(prep_res)
                return prep_res
        
        shared = {
            'input_numbers': list(range(4))  # [0, 1, 2, 3]
        }
        
        processor = OrderTrackingProcessor()
        self.loop.run_until_complete(processor.run_async(shared))
        
        # Odd numbers should finish before even numbers due to shorter delay
        self.assertLess(execution_order.index(1), execution_order.index(0))
        self.assertLess(execution_order.index(3), execution_order.index(2))

if __name__ == '__main__':
    unittest.main()