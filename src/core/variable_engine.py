"""
Variable Engine Module
Handles variable substitution, conditional sections, and complex logic
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum


class ConditionOperator(Enum):
    """Operators for conditional expressions"""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    IN = "in"
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class Variable:
    """Definition of a template variable"""
    name: str
    type: str  # string, number, date, boolean, list, object
    required: bool = False
    default: Optional[Any] = None
    description: str = ""
    example: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    validation: Optional[str] = None  # Regex pattern for validation


@dataclass
class Condition:
    """A conditional expression for section inclusion"""
    expression: str
    include_section: str
    else_section: Optional[str] = None


@dataclass
class ClientProfile:
    """Client-specific variable values and metadata"""
    id: str
    name: str
    variables: Dict[str, Any] = field(default_factory=dict)

    # Organization characteristics
    size_tier: str = "medium"  # solopreneur, small, medium, enterprise
    employee_count: int = 100
    industry: str = "technology"
    location: str = "US"

    # Compliance targets
    target_frameworks: List[str] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a variable value"""
        if key in self.variables:
            return self.variables[key]

        # Check computed properties
        if key == 'organization.size':
            return self.employee_count
        if key == 'organization.size_tier':
            return self.size_tier
        if key == 'organization.industry':
            return self.industry
        if key == 'compliance':
            return self.target_frameworks

        return default


class VariableEngine:
    """
    Handles all variable substitution and conditional logic
    Supports:
    - Simple {{VARIABLE}} substitution
    - Conditional {{#if condition}}...{{/if}} blocks
    - Complex expressions with AND/OR/NOT
    - Computed variables
    - Nested conditions
    """

    # Regex patterns
    SIMPLE_VAR_PATTERN = re.compile(r'\{\{([A-Z_]+)\}\}')
    CONDITIONAL_PATTERN = re.compile(
        r'\{\{#if\s+(.+?)\}\}(.*?)(?:\{\{#else\}\}(.*?))?\{\{/if\}\}',
        re.DOTALL
    )
    EACH_PATTERN = re.compile(
        r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}',
        re.DOTALL
    )

    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        self.computed: Dict[str, Callable] = {}
        self._load_default_variables()

    def _load_default_variables(self) -> None:
        """Load default variable definitions"""
        defaults = [
            Variable(
                name='ORGANIZATION_NAME',
                type='string',
                required=True,
                description='Legal name of the organization',
                example='Acme Corporation'
            ),
            Variable(
                name='EFFECTIVE_DATE',
                type='date',
                required=True,
                description='Date the policy becomes effective',
                example='January 1, 2025'
            ),
            Variable(
                name='APPROVAL_DATE',
                type='date',
                required=True,
                description='Date the policy was approved',
                example='December 15, 2024'
            ),
            Variable(
                name='APPROVER',
                type='string',
                default='Policy Committee',
                description='Person or committee approving the policy'
            ),
            Variable(
                name='VERSION',
                type='string',
                default='1.0',
                description='Policy version number'
            ),
            Variable(
                name='CSO_TITLE',
                type='string',
                default='Chief Security Officer',
                alternatives=['CISO', 'VP of Security', 'Security Director'],
                description='Title of the chief security officer'
            ),
            Variable(
                name='EXEC_MGMT',
                type='string',
                default='Executive Management',
                alternatives=['Executive Leadership', 'Senior Leadership Team'],
                description='Term for executive management'
            ),
            Variable(
                name='IT_STAFF',
                type='string',
                default='IT Staff',
                alternatives=['IT Department', 'Technology Team'],
                description='Term for IT personnel'
            ),
            Variable(
                name='RMO_TITLE',
                type='string',
                default='Risk Management Officer',
                description='Title of risk management officer'
            ),
            Variable(
                name='PRIVACY_OFFICER',
                type='string',
                required=False,
                description='Name of privacy officer (required for HIPAA/GDPR)'
            ),
            Variable(
                name='HR_DEPARTMENT',
                type='string',
                default='Human Resources',
                description='Term for HR department'
            ),
            Variable(
                name='LEGAL_DEPARTMENT',
                type='string',
                default='Legal Department',
                description='Term for legal department'
            ),
            Variable(
                name='REVIEW_DATE',
                type='date',
                description='Next scheduled review date'
            ),
            Variable(
                name='COMPANY_ADDRESS',
                type='string',
                description='Organization headquarters address'
            ),
            Variable(
                name='CONTACT_EMAIL',
                type='string',
                description='Primary contact email'
            )
        ]

        for var in defaults:
            self.variables[var.name] = var

    def register_variable(self, variable: Variable) -> None:
        """Register a new variable definition"""
        self.variables[variable.name] = variable

    def register_computed(self, name: str, func: Callable) -> None:
        """Register a computed variable"""
        self.computed[name] = func

    def render(self, template: str, client: ClientProfile) -> str:
        """
        Render a template with client variables

        Args:
            template: Template string with variables and conditionals
            client: Client profile with variable values

        Returns:
            Rendered string with all substitutions applied
        """
        result = template

        # Process conditionals first (may contain variables)
        result = self._process_conditionals(result, client)

        # Process each loops
        result = self._process_each(result, client)

        # Process simple variable substitution
        result = self._substitute_variables(result, client)

        # Clean up any remaining unsubstituted variables
        result = self._cleanup_unsubstituted(result)

        return result

    def _substitute_variables(self, text: str, client: ClientProfile) -> str:
        """Replace {{VARIABLE}} patterns with values"""

        def replace(match):
            var_name = match.group(1)

            # Check client variables first
            value = client.get(var_name)
            if value is not None:
                return str(value)

            # Check computed variables
            if var_name in self.computed:
                return str(self.computed[var_name](client))

            # Check defaults
            if var_name in self.variables:
                var_def = self.variables[var_name]
                if var_def.default is not None:
                    return str(var_def.default)

            # Return placeholder
            return f"[{var_name}]"

        return self.SIMPLE_VAR_PATTERN.sub(replace, text)

    def _process_conditionals(self, text: str, client: ClientProfile) -> str:
        """Process {{#if}}...{{/if}} blocks"""

        def replace(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            else_content = match.group(3) or ""

            if self._evaluate_condition(condition, client):
                return if_content.strip()
            else:
                return else_content.strip()

        # Process nested conditionals from innermost out
        prev = None
        while prev != text:
            prev = text
            text = self.CONDITIONAL_PATTERN.sub(replace, text)

        return text

    def _process_each(self, text: str, client: ClientProfile) -> str:
        """Process {{#each}}...{{/each}} loops"""

        def replace(match):
            list_name = match.group(1)
            content = match.group(2)

            items = client.get(list_name, [])
            if not isinstance(items, list):
                return ""

            results = []
            for item in items:
                # Replace {{this}} with item value
                rendered = content.replace('{{this}}', str(item))
                results.append(rendered.strip())

            return '\n'.join(results)

        return self.EACH_PATTERN.sub(replace, text)

    def _evaluate_condition(self, condition: str, client: ClientProfile) -> bool:
        """
        Evaluate a conditional expression

        Supports:
        - organization.size >= 500
        - organization.industry == "healthcare"
        - compliance.includes("pci_dss")
        - organization.size >= 50 and organization.industry == "healthcare"
        """
        condition = condition.strip()

        # Handle AND/OR
        if ' and ' in condition.lower():
            parts = re.split(r'\s+and\s+', condition, flags=re.IGNORECASE)
            return all(self._evaluate_condition(p, client) for p in parts)

        if ' or ' in condition.lower():
            parts = re.split(r'\s+or\s+', condition, flags=re.IGNORECASE)
            return any(self._evaluate_condition(p, client) for p in parts)

        # Handle NOT
        if condition.lower().startswith('not '):
            return not self._evaluate_condition(condition[4:], client)

        # Handle includes/contains
        includes_match = re.match(r'(\w+(?:\.\w+)?)\s*\.\s*includes\s*\(\s*["\'](.+?)["\']\s*\)', condition)
        if includes_match:
            list_name = includes_match.group(1)
            value = includes_match.group(2)
            items = client.get(list_name, [])
            if isinstance(items, list):
                return value in items
            return False

        # Handle comparison operators
        for op in ['>=', '<=', '!=', '==', '>', '<']:
            if op in condition:
                parts = condition.split(op, 1)
                if len(parts) == 2:
                    left = self._get_value(parts[0].strip(), client)
                    right = self._get_value(parts[1].strip(), client)
                    return self._compare(left, right, op)

        # Handle simple boolean
        value = client.get(condition)
        if value is not None:
            return bool(value)

        return False

    def _get_value(self, expr: str, client: ClientProfile) -> Any:
        """Get value from expression (variable name or literal)"""
        expr = expr.strip()

        # String literal
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]

        # Number literal
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Boolean literal
        if expr.lower() == 'true':
            return True
        if expr.lower() == 'false':
            return False

        # Variable reference
        return client.get(expr)

    def _compare(self, left: Any, right: Any, op: str) -> bool:
        """Compare two values with operator"""
        try:
            if op == '==':
                return left == right
            elif op == '!=':
                return left != right
            elif op == '>':
                return left > right
            elif op == '<':
                return left < right
            elif op == '>=':
                return left >= right
            elif op == '<=':
                return left <= right
        except TypeError:
            return False
        return False

    def _cleanup_unsubstituted(self, text: str) -> str:
        """Mark remaining unsubstituted variables"""
        # Convert remaining {{VAR}} to [VAR - REQUIRED]
        def mark_missing(match):
            var_name = match.group(1)
            if var_name in self.variables and self.variables[var_name].required:
                return f"[{var_name} - REQUIRED]"
            return f"[{var_name}]"

        return self.SIMPLE_VAR_PATTERN.sub(mark_missing, text)

    def validate_client(self, client: ClientProfile) -> List[str]:
        """
        Validate that client has all required variables

        Returns:
            List of missing required variable names
        """
        missing = []

        for name, var in self.variables.items():
            if var.required:
                value = client.get(name)
                if value is None or value == '':
                    missing.append(name)

        return missing

    def get_required_variables(self) -> List[Variable]:
        """Get list of required variables"""
        return [v for v in self.variables.values() if v.required]

    def get_optional_variables(self) -> List[Variable]:
        """Get list of optional variables"""
        return [v for v in self.variables.values() if not v.required]
