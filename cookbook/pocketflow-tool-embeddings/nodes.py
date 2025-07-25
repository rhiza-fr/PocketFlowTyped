from tools.embeddings import get_embedding

from pocketflow import Node


class EmbeddingNode(Node):
    """Node for getting embeddings from OpenAI API"""
    
    def prep(self, shared):
        # Get text from shared store
        return shared.get("text", "")
        
    def exec(self, prep_res):
        # Get embedding using tool function
        return get_embedding(prep_res)
        
    def post(self, shared, prep_res, exec_res):
        # Store embedding in shared store
        shared["embedding"] = exec_res
        return "default" 