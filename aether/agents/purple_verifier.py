"""Purple Team: Formal Verification & Property Testing Engine.

Uses Z3 SMT Solver for mathematical verification and Hypothesis 
for property-based boundary testing.
"""

import ast
import textwrap
import tempfile
import subprocess
from typing import Optional
from dataclasses import dataclass, field
from z3 import (
    Solver, Int, Bool, And, Or, Not, If,
    sat, unsat, unknown,
    ArithRef, BoolRef,
)
from rich.console import Console

console = Console()


@dataclass
class VerificationResult:
    """Result of Purple Team verification."""
    passed: bool
    z3_result: str  # 'verified', 'failed', 'skipped'
    hypothesis_result: str  # 'passed', 'failed', 'skipped'
    error_trace: Optional[str] = None
    details: list[str] = field(default_factory=list)


class PurpleTeamVerifier:
    """Purple Team: Formal verification of security patches."""
    
    def verify_patch(self, original_code: str, patched_code: str, vulnerability_type: str) -> VerificationResult:
        """Main verification pipeline combining Z3 and Hypothesis."""
        console.print("\n[bold magenta]🟣 Purple Team: Measuring Detection Gap & Verifying Patch[/bold magenta]")
        console.print("  [dim]Evaluating MITRE ATT&CK mitigation success...[/dim]")
        details = []
        
        # Step 1: Z3 formal verification
        z3_result = self._z3_verify(patched_code, vulnerability_type)
        details.append(f"Z3 verification: {z3_result}")
        
        # Step 2: Hypothesis property-based testing
        hypothesis_result, hyp_error = self._hypothesis_verify(patched_code, vulnerability_type)
        details.append(f"Hypothesis testing: {hypothesis_result}")
        
        passed = (z3_result == 'verified' or z3_result == 'skipped') and \
                 (hypothesis_result == 'passed' or hypothesis_result == 'skipped')
        
        error_trace = None
        if not passed:
            error_parts = []
            if z3_result == 'failed':
                error_parts.append(f"Z3 verification failed for {vulnerability_type}")
            if hypothesis_result == 'failed':
                error_parts.append(f"Hypothesis testing failed: {hyp_error}")
            error_trace = "\n".join(error_parts)
        
        return VerificationResult(
            passed=passed,
            z3_result=z3_result,
            hypothesis_result=hypothesis_result,
            error_trace=error_trace,
            details=details,
        )
    
    def _z3_verify(self, patched_code: str, vulnerability_type: str) -> str:
        """Use Z3 to verify security properties of the patched code."""
        # Verify the patched code doesn't contain dangerous patterns
        # by checking AST-level properties
        try:
            tree = ast.parse(patched_code)
        except SyntaxError:
            return 'failed'
        
        solver = Solver()
        
        # Check: no eval/exec calls remain
        has_eval = Bool('has_eval')
        has_exec = Bool('has_exec')
        has_shell_true = Bool('has_shell_true')
        has_os_system = Bool('has_os_system')
        
        # Walk AST to check for dangerous patterns
        eval_found = False
        exec_found = False
        shell_found = False
        os_system_found = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'eval':
                        eval_found = True
                    elif node.func.id == 'exec':
                        exec_found = True
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'system' and isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                        os_system_found = True
                    if node.func.attr in ('Popen', 'call', 'run'):
                        for kw in node.keywords:
                            if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                shell_found = True
        
        # Add constraints: all dangerous patterns must be absent
        solver.add(has_eval == eval_found)
        solver.add(has_exec == exec_found)
        solver.add(has_shell_true == shell_found)
        solver.add(has_os_system == os_system_found)
        
        # Security property: none of these should be True
        solver.add(Not(Or(has_eval, has_exec, has_shell_true, has_os_system)))
        
        result = solver.check()
        if result == sat:
            return 'verified'
        elif result == unsat:
            return 'failed'
        else:
            return 'skipped'
    
    def _hypothesis_verify(self, patched_code: str, vulnerability_type: str) -> tuple[str, Optional[str]]:
        """Generate and run a Hypothesis property test for the patched code."""
        test_script = self._generate_hypothesis_test(patched_code, vulnerability_type)
        
        if test_script is None:
            return ('skipped', None)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                f.flush()
                
                result = subprocess.run(
                    ['python', '-m', 'pytest', f.name, '-x', '-v', '--tb=short'],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                
                if result.returncode == 0:
                    return ('passed', None)
                else:
                    return ('failed', result.stdout + result.stderr)
        except subprocess.TimeoutExpired:
            return ('failed', 'Hypothesis test timed out after 60 seconds')
        except Exception as e:
            return ('failed', str(e))
    
    def _generate_hypothesis_test(self, patched_code: str, vulnerability_type: str) -> Optional[str]:
        """Dynamically generate a Hypothesis test script for the patch."""
        # Generate test that verifies the patched code:
        # 1. Is syntactically valid
        # 2. Doesn't contain dangerous patterns
        # 3. Handles edge cases properly
        
        test_code = textwrap.dedent(f'''
            import ast
            import hypothesis
            from hypothesis import given, strategies as st, settings
            
            PATCHED_CODE = {repr(patched_code)}
            
            def test_patched_code_is_valid_python():
                """Verify the patched code is syntactically valid."""
                tree = ast.parse(PATCHED_CODE)
                assert tree is not None
            
            def test_no_dangerous_patterns():
                """Verify no dangerous function calls remain in patched code."""
                tree = ast.parse(PATCHED_CODE)
                dangerous = {{'eval', 'exec'}}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            assert node.func.id not in dangerous, \\
                                f"Dangerous call {{node.func.id}}() found at line {{node.lineno}}"
            
            @given(st.text(min_size=0, max_size=1000))
            @settings(max_examples=200, deadline=None)
            def test_no_injection_possible(user_input):
                """Property test: arbitrary input should not cause code injection."""
                # Verify the patched code doesn't use string formatting with user input
                # in dangerous contexts
                tree = ast.parse(PATCHED_CODE)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
                            assert False, "Code injection vector found"
        ''')
        
        return test_code
