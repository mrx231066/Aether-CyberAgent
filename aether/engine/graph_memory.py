import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Any
import networkx as nx

class CodeGraphMemory:
    """
    Graph-based memory representation of the codebase using networkx.
    Tracks dependencies between Python files to analyze blast radius and relationships.
    """
    
    def __init__(self) -> None:
        """Initialize the graph memory with a directed graph."""
        self.graph = nx.DiGraph()
        self.module_to_file: Dict[str, str] = {}
        
    def _get_module_name(self, file_path: Path, root_path: Path) -> str:
        """Convert a file path to a probable module name."""
        try:
            rel_path = file_path.relative_to(root_path)
            parts = list(rel_path.parts)
            if parts[-1] == "__init__.py":
                parts.pop()
            else:
                parts[-1] = parts[-1].replace(".py", "")
            return ".".join(parts)
        except ValueError:
            # Fallback if not relative
            return file_path.stem

    def build_from_directory(self, path: str) -> None:
        """
        Walk through a directory, parse all .py files for imports,
        and build a dependency graph.
        """
        root_path = Path(path).resolve()
        
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        # First pass: map files to module names and add nodes
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    abs_path = str(file_path.resolve())
                    module_name = self._get_module_name(file_path, root_path)
                    
                    self.module_to_file[module_name] = abs_path
                    self.graph.add_node(abs_path, module=module_name, type="file")

        # Second pass: parse AST and add edges
        for module_name, abs_path in self.module_to_file.items():
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=abs_path)
                
                # Find imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._add_dependency(abs_path, alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Handle relative imports roughly
                            if node.level > 0:
                                parts = module_name.split('.')
                                # Drop level parts from current module name
                                base_module = ".".join(parts[:-node.level]) if len(parts) > node.level else ""
                                full_module = f"{base_module}.{node.module}" if base_module else node.module
                            else:
                                full_module = node.module
                            self._add_dependency(abs_path, full_module)
                            
            except (SyntaxError, UnicodeDecodeError, OSError):
                # Skip files that cannot be parsed
                continue

    def _add_dependency(self, source_file: str, imported_module: str) -> None:
        """Add an edge if the imported module is in our codebase."""
        # Check direct match
        target_file = self.module_to_file.get(imported_module)
        
        # Check if it's importing a submodule of a known package
        if not target_file:
            parts = imported_module.split('.')
            for i in range(len(parts), 0, -1):
                sub_module = ".".join(parts[:i])
                if sub_module in self.module_to_file:
                    target_file = self.module_to_file[sub_module]
                    break
                    
        if target_file and source_file != target_file:
            # Edge: source_file depends on target_file
            self.graph.add_edge(source_file, target_file)

    def get_blast_radius(self, file_path: str) -> Dict[str, Any]:
        """
        Calculate the blast radius of a vulnerable file.
        Returns files that depend on this file (ancestors in dependency graph).
        """
        abs_path = str(Path(file_path).resolve())
        if abs_path not in self.graph:
            return {
                "affected_files": [],
                "depth": 0,
                "risk_score": 0.0
            }
            
        try:
            # Ancestors are nodes that have a path to this node
            # (i.e. files that depend on this file)
            affected = list(nx.ancestors(self.graph, abs_path))
            
            # Calculate depth (longest shortest path from any ancestor to this node)
            max_depth = 0
            if affected:
                for ancestor in affected:
                    try:
                        path_len = nx.shortest_path_length(self.graph, source=ancestor, target=abs_path)
                        max_depth = max(max_depth, path_len)
                    except nx.NetworkXNoPath:
                        continue
                        
            # Risk score heuristic based on number of affected files and total graph size
            total_nodes = max(1, self.graph.number_of_nodes())
            risk_score = min(10.0, (len(affected) / total_nodes) * 10.0 + (len(affected) * 0.5))
            
            return {
                "affected_files": affected,
                "depth": max_depth,
                "risk_score": round(risk_score, 2)
            }
        except nx.NetworkXError:
            return {
                "affected_files": [],
                "depth": 0,
                "risk_score": 0.0
            }

    def get_dependency_tree(self) -> Dict[str, List[str]]:
        """Return the full graph as an adjacency dict for visualization."""
        return nx.to_dict_of_lists(self.graph)

    def get_file_nodes(self) -> List[str]:
        """Return all file nodes in the graph."""
        return list(self.graph.nodes())
