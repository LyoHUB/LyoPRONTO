"""
Smoke tests for legacy example scripts.

These tests verify that the legacy example scripts (examples/legacy/ex_knownRp_PD.py,
ex_unknownRp_PD.py) still run without errors. They provide basic coverage for validation
modules like calc_unknownRp.py.

Tests:
    - test_ex_knownRp_execution: Verifies ex_knownRp_PD.py runs successfully
    - test_ex_unknownRp_execution: Verifies ex_unknownRp_PD.py runs successfully with test data

Coverage Impact:
    - Provides smoke test coverage for calc_unknownRp.py (now 89%)
    - Validates validation module code paths work in real-world scenarios
"""

import pytest
import papermill as pm


class TestDocsNotebooks:
    """Smoke tests: run example scripts used for documentation."""

    @pytest.mark.notebook
    def test_knownRp_notebook_execution(self, repo_root):
        """Test that ex_knownRp_PD.py runs without error."""
        pm.execute_notebook(
            repo_root / "docs/examples/knownRp_PD.ipynb",
            repo_root / "docs/examples/knownRp_PD_output.ipynb",
        )
        # Will error if execution fails

    @pytest.mark.notebook
    def test_unknownRp_notebook_execution(self, repo_root):
        """Test that ex_knownRp_PD.py runs without error."""
        pm.execute_notebook(
            repo_root / "docs/examples/unknownRp_PD.ipynb",
            repo_root / "docs/examples/unknownRp_PD_output.ipynb",
            parameters=dict(data_path=str(repo_root / "docs" / "examples") + "/"),
        )
        # Will error if execution fails
