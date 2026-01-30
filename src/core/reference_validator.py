"""
Reference Validator Module
Validates cross-references between policies
Ensures referenced policies exist and are not circular
"""

import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict


class ValidationMode(Enum):
    """How to handle broken references"""
    BLOCK = "block"           # Stop generation if broken references
    WARN = "warn"             # Continue with warnings
    AUTO_INCLUDE = "auto"     # Automatically include referenced policies
    CONFIGURABLE = "config"   # Per-client/per-generation setting


class ReferenceStatus(Enum):
    """Status of a reference"""
    VALID = "valid"
    BROKEN = "broken"
    DEPRECATED = "deprecated"
    CIRCULAR = "circular"
    VERSION_MISMATCH = "version_mismatch"


@dataclass
class ReferenceIssue:
    """Represents an issue with a policy reference"""
    source_policy: str
    referenced_policy: str
    status: ReferenceStatus
    message: str
    severity: str = "warning"  # warning, error, info


@dataclass
class ValidationResult:
    """Result of reference validation"""
    is_valid: bool
    issues: List[ReferenceIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    auto_include: List[str] = field(default_factory=list)
    circular_chains: List[List[str]] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        """Check if generation should be blocked"""
        return len(self.errors) > 0


class ReferenceValidator:
    """
    Validates cross-references between policies
    Detects broken references, circular dependencies, and deprecated links
    """

    def __init__(self, policy_library: Dict[str, 'Policy'] = None):
        """
        Initialize validator

        Args:
            policy_library: Dictionary of policy_id -> Policy objects
        """
        self.policy_library = policy_library or {}
        self._reference_graph: Dict[str, Set[str]] = defaultdict(set)
        self._deprecated_policies: Set[str] = set()

    def set_policy_library(self, library: Dict[str, 'Policy']) -> None:
        """Set the policy library to validate against"""
        self.policy_library = library
        self._build_reference_graph()

    def add_policy(self, policy_id: str, references: List[str]) -> None:
        """Add a policy and its references to the graph"""
        self._reference_graph[policy_id] = set(references)

    def mark_deprecated(self, policy_id: str) -> None:
        """Mark a policy as deprecated"""
        self._deprecated_policies.add(policy_id)

    def _build_reference_graph(self) -> None:
        """Build reference graph from policy library"""
        self._reference_graph.clear()
        self._deprecated_policies.clear()

        for policy_id, policy in self.policy_library.items():
            self._reference_graph[policy_id] = set(policy.references)

            if hasattr(policy, 'status') and policy.status.value == 'deprecated':
                self._deprecated_policies.add(policy_id)

    def validate_policy(self, policy_id: str,
                       mode: ValidationMode = ValidationMode.WARN) -> ValidationResult:
        """
        Validate references for a single policy

        Args:
            policy_id: ID of policy to validate
            mode: How to handle issues

        Returns:
            ValidationResult with issues found
        """
        result = ValidationResult(is_valid=True)

        if policy_id not in self.policy_library:
            result.errors.append(f"Policy not found: {policy_id}")
            result.is_valid = False
            return result

        policy = self.policy_library[policy_id]
        references = policy.references if hasattr(policy, 'references') else []

        for ref in references:
            issue = self._validate_reference(policy_id, ref, mode)
            if issue:
                result.issues.append(issue)

                if issue.status == ReferenceStatus.BROKEN:
                    if mode == ValidationMode.BLOCK:
                        result.errors.append(issue.message)
                        result.is_valid = False
                    elif mode == ValidationMode.AUTO_INCLUDE:
                        result.auto_include.append(ref)
                        result.warnings.append(f"Will auto-include: {ref}")
                    else:
                        result.warnings.append(issue.message)

                elif issue.status == ReferenceStatus.DEPRECATED:
                    result.warnings.append(issue.message)

                elif issue.status == ReferenceStatus.CIRCULAR:
                    result.errors.append(issue.message)
                    result.is_valid = False

        return result

    def validate_all(self, mode: ValidationMode = ValidationMode.WARN) -> ValidationResult:
        """
        Validate all policies in the library

        Args:
            mode: How to handle issues

        Returns:
            Combined ValidationResult for all policies
        """
        result = ValidationResult(is_valid=True)

        # Check for circular references first
        circular = self._find_circular_references()
        if circular:
            result.circular_chains = circular
            for chain in circular:
                chain_str = ' -> '.join(chain)
                result.issues.append(ReferenceIssue(
                    source_policy=chain[0],
                    referenced_policy=chain[-1],
                    status=ReferenceStatus.CIRCULAR,
                    message=f"Circular reference detected: {chain_str}",
                    severity="error"
                ))
                result.errors.append(f"Circular reference: {chain_str}")
            result.is_valid = False

        # Validate each policy
        for policy_id in self.policy_library:
            policy_result = self.validate_policy(policy_id, mode)

            result.issues.extend(policy_result.issues)
            result.warnings.extend(policy_result.warnings)
            result.errors.extend(policy_result.errors)
            result.auto_include.extend(policy_result.auto_include)

            if not policy_result.is_valid:
                result.is_valid = False

        # Deduplicate auto_include
        result.auto_include = list(set(result.auto_include))

        return result

    def _validate_reference(self, source: str, target: str,
                           mode: ValidationMode) -> Optional[ReferenceIssue]:
        """Validate a single reference"""
        # Check if target exists
        if target not in self.policy_library:
            return ReferenceIssue(
                source_policy=source,
                referenced_policy=target,
                status=ReferenceStatus.BROKEN,
                message=f"Policy '{source}' references non-existent policy '{target}'",
                severity="error" if mode == ValidationMode.BLOCK else "warning"
            )

        # Check if target is deprecated
        if target in self._deprecated_policies:
            return ReferenceIssue(
                source_policy=source,
                referenced_policy=target,
                status=ReferenceStatus.DEPRECATED,
                message=f"Policy '{source}' references deprecated policy '{target}'",
                severity="warning"
            )

        return None

    def _find_circular_references(self) -> List[List[str]]:
        """
        Find all circular reference chains using DFS

        Returns:
            List of circular chains (each chain is a list of policy IDs)
        """
        circular_chains = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found cycle - extract it
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                circular_chains.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._reference_graph.get(node, set()):
                dfs(neighbor, path)

            path.pop()
            rec_stack.remove(node)

        for policy_id in self._reference_graph:
            if policy_id not in visited:
                dfs(policy_id, [])

        return circular_chains

    def get_all_references(self, policy_id: str,
                          include_transitive: bool = True) -> Set[str]:
        """
        Get all policies referenced by a policy

        Args:
            policy_id: Policy to check
            include_transitive: Include indirect references

        Returns:
            Set of referenced policy IDs
        """
        if policy_id not in self._reference_graph:
            return set()

        direct = self._reference_graph[policy_id].copy()

        if not include_transitive:
            return direct

        # BFS for transitive references
        all_refs = direct.copy()
        queue = list(direct)

        while queue:
            current = queue.pop(0)
            if current in self._reference_graph:
                for ref in self._reference_graph[current]:
                    if ref not in all_refs and ref != policy_id:
                        all_refs.add(ref)
                        queue.append(ref)

        return all_refs

    def get_dependents(self, policy_id: str) -> Set[str]:
        """
        Get all policies that reference a given policy

        Args:
            policy_id: Policy to check

        Returns:
            Set of dependent policy IDs
        """
        dependents = set()

        for source, refs in self._reference_graph.items():
            if policy_id in refs:
                dependents.add(source)

        return dependents

    def get_orphaned_policies(self) -> Set[str]:
        """
        Find policies that are never referenced by any other policy

        Returns:
            Set of orphaned policy IDs
        """
        all_policies = set(self._reference_graph.keys())
        referenced = set()

        for refs in self._reference_graph.values():
            referenced.update(refs)

        return all_policies - referenced

    def get_missing_policies(self) -> Set[str]:
        """
        Find policies that are referenced but don't exist

        Returns:
            Set of missing policy IDs
        """
        existing = set(self._reference_graph.keys())
        referenced = set()

        for refs in self._reference_graph.values():
            referenced.update(refs)

        return referenced - existing

    def generate_report(self) -> str:
        """Generate a validation report"""
        lines = ["# Policy Reference Validation Report", ""]

        # Summary
        total = len(self._reference_graph)
        orphaned = self.get_orphaned_policies()
        missing = self.get_missing_policies()
        circular = self._find_circular_references()

        lines.append("## Summary")
        lines.append(f"- Total policies: {total}")
        lines.append(f"- Orphaned policies (never referenced): {len(orphaned)}")
        lines.append(f"- Missing policies (referenced but don't exist): {len(missing)}")
        lines.append(f"- Circular reference chains: {len(circular)}")
        lines.append("")

        # Missing policies
        if missing:
            lines.append("## Missing Policies")
            lines.append("These policies are referenced but don't exist:")
            for policy_id in sorted(missing):
                # Find what references them
                dependents = self.get_dependents(policy_id)
                lines.append(f"- **{policy_id}** (referenced by: {', '.join(sorted(dependents))})")
            lines.append("")

        # Circular references
        if circular:
            lines.append("## Circular References")
            for chain in circular:
                lines.append(f"- {' -> '.join(chain)}")
            lines.append("")

        # Orphaned policies
        if orphaned:
            lines.append("## Orphaned Policies")
            lines.append("These policies are never referenced by any other policy:")
            for policy_id in sorted(orphaned):
                lines.append(f"- {policy_id}")
            lines.append("")

        return '\n'.join(lines)
