"""
Knowledge Base for SolidWorks operations using ChromaDB

Stores and retrieves CAD operations, patterns, and best practices
to provide context for AI-assisted automation.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class SolidWorksKnowledgeBase:
    """Knowledge base for storing and retrieving SolidWorks operations"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and collections"""
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use sentence transformer for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize collections
        self._init_collections()

    def _init_collections(self):
        """Initialize ChromaDB collections"""
        # Collection for operations (what was done)
        self.operations_collection = self.client.get_or_create_collection(
            name="solidworks_operations",
            embedding_function=self.embedding_function,
            metadata={"description": "SolidWorks operations and their outcomes"}
        )
        
        # Collection for design patterns
        self.patterns_collection = self.client.get_or_create_collection(
            name="design_patterns",
            embedding_function=self.embedding_function,
            metadata={"description": "Common design patterns and best practices"}
        )
        
        # Collection for errors and solutions
        self.errors_collection = self.client.get_or_create_collection(
            name="errors_solutions",
            embedding_function=self.embedding_function,
            metadata={"description": "Common errors and their solutions"}
        )
        
        # Collection for VBA macros
        self.macros_collection = self.client.get_or_create_collection(
            name="vba_macros",
            embedding_function=self.embedding_function,
            metadata={"description": "VBA macro patterns and usage"}
        )

    async def store_operation(
        self,
        operation: str,
        context: Dict[str, Any],
        result: Dict[str, Any],
        success: bool,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store a SolidWorks operation and its outcome"""
        operation_id = self._generate_id(operation, context)
        
        document = {
            "operation": operation,
            "context": json.dumps(context),
            "result": json.dumps(result),
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or []
        }
        
        # Create searchable text
        search_text = f"{operation} {' '.join(tags or [])} {context.get('description', '')}"
        
        self.operations_collection.add(
            documents=[search_text],
            metadatas=[document],
            ids=[operation_id]
        )
        
        logger.info(f"Stored operation: {operation_id}")
        return operation_id

    async def store_design_pattern(
        self,
        name: str,
        description: str,
        pattern_type: str,
        implementation: Dict[str, Any],
        examples: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Store a design pattern"""
        pattern_id = self._generate_id(name, {"type": pattern_type})
        
        document = {
            "name": name,
            "description": description,
            "pattern_type": pattern_type,
            "implementation": json.dumps(implementation),
            "examples": json.dumps(examples or []),
            "timestamp": datetime.now().isoformat()
        }
        
        search_text = f"{name} {description} {pattern_type}"
        
        self.patterns_collection.add(
            documents=[search_text],
            metadatas=[document],
            ids=[pattern_id]
        )
        
        return pattern_id

    async def store_error_solution(
        self,
        error_message: str,
        error_context: Dict[str, Any],
        solution: str,
        solution_steps: List[str]
    ) -> str:
        """Store an error and its solution"""
        error_id = self._generate_id(error_message, error_context)
        
        document = {
            "error_message": error_message,
            "error_context": json.dumps(error_context),
            "solution": solution,
            "solution_steps": json.dumps(solution_steps),
            "timestamp": datetime.now().isoformat()
        }
        
        search_text = f"{error_message} {solution}"
        
        self.errors_collection.add(
            documents=[search_text],
            metadatas=[document],
            ids=[error_id]
        )
        
        return error_id

    async def store_macro_pattern(
        self,
        macro_name: str,
        description: str,
        code_snippet: str,
        use_cases: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a VBA macro pattern"""
        macro_id = self._generate_id(macro_name, {"type": "vba"})
        
        document = {
            "macro_name": macro_name,
            "description": description,
            "code_snippet": code_snippet,
            "use_cases": json.dumps(use_cases),
            "parameters": json.dumps(parameters or {}),
            "timestamp": datetime.now().isoformat()
        }
        
        search_text = f"{macro_name} {description} {' '.join(use_cases)}"
        
        self.macros_collection.add(
            documents=[search_text],
            metadatas=[document],
            ids=[macro_id]
        )
        
        return macro_id

    async def find_similar_operations(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find similar operations based on query"""
        results = self.operations_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters
        )
        
        return self._format_results(results)

    async def find_design_patterns(
        self,
        query: str,
        pattern_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant design patterns"""
        filters = {"pattern_type": pattern_type} if pattern_type else None
        
        results = self.patterns_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters
        )
        
        return self._format_results(results)

    async def find_error_solutions(
        self,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Find solutions for similar errors"""
        query = f"{error_message} {json.dumps(context or {})}"
        
        results = self.errors_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return self._format_results(results)

    async def find_macro_patterns(
        self,
        use_case: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant VBA macro patterns"""
        results = self.macros_collection.query(
            query_texts=[use_case],
            n_results=n_results
        )
        
        return self._format_results(results)

    async def get_operation_history(
        self,
        limit: int = 10,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get recent operation history"""
        filters = {"success": True} if success_only else None
        
        # ChromaDB doesn't support direct sorting, so we get more and sort
        results = self.operations_collection.get(
            limit=limit * 2,
            where=filters
        )
        
        # Format and sort by timestamp
        formatted = self._format_results({"metadatas": [results["metadatas"]]})
        formatted.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return formatted[:limit]

    async def analyze_operation_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in stored operations"""
        all_operations = self.operations_collection.get()
        
        if not all_operations["metadatas"]:
            return {"total_operations": 0}
        
        # Analyze success rate
        total = len(all_operations["metadatas"])
        successful = sum(1 for op in all_operations["metadatas"] if op.get("success", False))
        
        # Count operation types
        operation_counts = {}
        for op in all_operations["metadatas"]:
            op_type = op.get("operation", "unknown")
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        # Find common tags
        tag_counts = {}
        for op in all_operations["metadatas"]:
            for tag in op.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "total_operations": total,
            "successful_operations": successful,
            "success_rate": successful / total if total > 0 else 0,
            "operation_types": operation_counts,
            "common_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }

    def _generate_id(self, primary: str, context: Dict[str, Any]) -> str:
        """Generate a unique ID for a document"""
        content = f"{primary}_{json.dumps(context, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format ChromaDB results into a clean structure"""
        formatted = []
        
        if "metadatas" in results and results["metadatas"]:
            for metadata_list in results["metadatas"]:
                for metadata in metadata_list:
                    # Parse JSON fields
                    for field in ["context", "result", "implementation", "examples", 
                                  "error_context", "solution_steps", "use_cases", "parameters"]:
                        if field in metadata and isinstance(metadata[field], str):
                            try:
                                metadata[field] = json.loads(metadata[field])
                            except json.JSONDecodeError:
                                pass
                    
                    formatted.append(metadata)
        
        return formatted

    async def export_knowledge(self, output_path: str):
        """Export all knowledge to a JSON file"""
        knowledge = {
            "operations": self._format_results({"metadatas": [self.operations_collection.get()["metadatas"]]}),
            "patterns": self._format_results({"metadatas": [self.patterns_collection.get()["metadatas"]]}),
            "errors": self._format_results({"metadatas": [self.errors_collection.get()["metadatas"]]}),
            "macros": self._format_results({"metadatas": [self.macros_collection.get()["metadatas"]]})
        }
        
        with open(output_path, 'w') as f:
            json.dump(knowledge, f, indent=2)
        
        logger.info(f"Exported knowledge to {output_path}")

    async def import_knowledge(self, input_path: str):
        """Import knowledge from a JSON file"""
        with open(input_path, 'r') as f:
            knowledge = json.load(f)
        
        # Import operations
        for op in knowledge.get("operations", []):
            await self.store_operation(
                op["operation"],
                op.get("context", {}),
                op.get("result", {}),
                op.get("success", False),
                op.get("tags", [])
            )
        
        # Import patterns
        for pattern in knowledge.get("patterns", []):
            await self.store_design_pattern(
                pattern["name"],
                pattern["description"],
                pattern["pattern_type"],
                pattern.get("implementation", {}),
                pattern.get("examples", [])
            )
        
        # Import errors
        for error in knowledge.get("errors", []):
            await self.store_error_solution(
                error["error_message"],
                error.get("error_context", {}),
                error["solution"],
                error.get("solution_steps", [])
            )
        
        # Import macros
        for macro in knowledge.get("macros", []):
            await self.store_macro_pattern(
                macro["macro_name"],
                macro["description"],
                macro["code_snippet"],
                macro.get("use_cases", []),
                macro.get("parameters", {})
            )
        
        logger.info(f"Imported knowledge from {input_path}")