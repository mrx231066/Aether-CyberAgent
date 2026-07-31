"""Comprehensive Verification Test Suite for Execution Guard, ActionExecutor, and Live Status Indicators."""

import pytest
from aether.engine.tools import ToolEngine
from aether.engine.action_executor import ActionExecutor
from aether.engine.guard_validator import CommandGuardValidator

def test_a_single_command_sanity_check():
    """Test A — Single command sanity check ("install curl")."""
    print("\n--- TEST A OUTPUT ---")
    executor = ActionExecutor()
    sample_response = "<bash>which curl || apt-get update && apt-get install -y curl || echo 'curl checked'</bash>"
    _, results = executor.process_and_execute_response(sample_response)
    assert len(results) == 1
    assert results[0]["success"] is True
    print(f"Tool Call Fired: execute_shell('{results[0]['command']}')")
    print(f"Exit Code: {results[0]['exit_code']}")
    print(f"Stdout:\n{results[0]['stdout'].strip()}")
    print("---------------------\n")

def test_b_multistep_setup():
    """Test B — Multi-step setup (Codex/Termux setup request)."""
    print("\n--- TEST B OUTPUT ---")
    executor = ActionExecutor()
    multi_step_response = """
Phase 1: Purge existing environment
<bash>echo "Purging old context..."</bash>

Phase 2: Install core tools
<bash>which git || echo "git verified"</bash>
<bash>which node || echo "node verified"</bash>

Phase 3: Verify environment
<bash>echo "Setup phase 3 complete"</bash>
"""
    _, results = executor.process_and_execute_response(multi_step_response)
    assert len(results) == 4
    for i, res in enumerate(results, 1):
        print(f"Tool Call #{i}: execute_shell('{res['command']}') -> Exit Code {res['exit_code']} | Stdout: {res['stdout'].strip()}")
        assert res["success"] is True
    print(f"Total Tool Executions: {len(results)} | Total Commands in Request: 4")
    print("---------------------\n")

def test_c_guard_validator():
    """Test C — Guard validator test (catching unexecuted commands & forcing retry)."""
    print("\n--- TEST C OUTPUT ---")
    unexecuted_text = """
To setup the environment, run:
```bash
pkg update -y
pkg install git nodejs -y
npm install -g @openai/codex
```
    """
    executed_actions = []  # ZERO tool calls made
    is_valid, reason = CommandGuardValidator.validate_turn(unexecuted_text, executed_actions)
    print(f"Response validation result: is_valid={is_valid}")
    print(f"Reason: {reason}")
    assert is_valid is False

    retry_prompt = CommandGuardValidator.get_retry_prompt()
    print(f"Catch-and-Retry Triggered -> Internal Re-prompt: '{retry_prompt}'")
    
    # Simulate agent receiving retry prompt and emitting real action tags
    corrected_response = "<bash>echo 'pkg update simulated'</bash><bash>echo 'pkg install git nodejs simulated'</bash>"
    executor = ActionExecutor()
    _, corrected_actions = executor.process_and_execute_response(corrected_response)
    is_valid_after_retry, _ = CommandGuardValidator.validate_turn(corrected_response, corrected_actions)
    assert is_valid_after_retry is True
    print(f"Post-Retry Validation: is_valid={is_valid_after_retry} | Executed Actions: {len(corrected_actions)}")
    print("---------------------\n")

def test_d_status_indicator_demo():
    """Test D — Status indicator demo (Success vs Failure)."""
    print("\n--- TEST D OUTPUT ---")
    tools = ToolEngine()
    
    print("[Success Case]")
    res_ok = tools.execute_shell("echo 'Status indicator success test'")
    assert res_ok["exit_code"] == 0
    
    print("\n[Failure Case]")
    res_fail = tools.execute_shell("non_existent_command_xyz_12345")
    assert res_fail["exit_code"] != 0
    print("---------------------\n")
