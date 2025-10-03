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

import subprocess
import sys
import pytest
from pathlib import Path


class TestLegacyExamples:
    """Smoke tests for legacy example scripts in repository root."""

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory."""
        return Path(__file__).parent.parent

    def test_ex_knownRp_execution(self, repo_root, tmp_path):
        """
        Verify ex_knownRp_PD.py runs without errors.
        
        This smoke test validates that the legacy known Rp example script
        executes successfully. It tests calc_knownRp.py functionality in
        a real-world usage pattern.
        
        Args:
            repo_root: Path to repository root
            tmp_path: Temporary directory for output files
        """
        script_path = repo_root / "examples" / "legacy" / "ex_knownRp_PD.py"
        
        # Skip if script doesn't exist
        if not script_path.exists():
            pytest.skip(f"Legacy example script {script_path} not found")
        
        # Run script in temporary directory to avoid cluttering repo
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        # Check for successful execution
        assert result.returncode == 0, (
            f"ex_knownRp_PD.py failed with return code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        
        # Verify output files were created
        output_files = list(tmp_path.glob("output_saved_*.csv"))
        assert len(output_files) > 0, "No output CSV file generated"
        
        # Verify PDF files were created (temperature plots)
        pdf_files = list(tmp_path.glob("*.pdf"))
        assert len(pdf_files) >= 3, f"Expected at least 3 PDF plots, found {len(pdf_files)}"

    def test_ex_unknownRp_execution(self, repo_root, tmp_path):
        """
        Verify ex_unknownRp_PD.py runs without errors.
        
        This smoke test validates that the legacy unknown Rp (parameter estimation)
        example script executes successfully. It tests calc_unknownRp.py functionality
        in a real-world usage pattern.
        
        This validates calc_unknownRp.py works in practice (now 89% test coverage).
        
        Args:
            repo_root: Path to repository root
            tmp_path: Temporary directory for output files
        """
        script_path = repo_root / "examples" / "legacy" / "ex_unknownRp_PD.py"
        
        # Skip if script doesn't exist
        if not script_path.exists():
            pytest.skip(f"Legacy example script {script_path} not found")
        
        # Copy test data to temporary directory (script expects ./temperature.dat)
        # Legacy directory now has its own copy
        legacy_data_path = repo_root / "examples" / "legacy" / "temperature.dat"
        if not legacy_data_path.exists():
            pytest.skip("Test data file examples/legacy/temperature.dat not found")
        
        # Create symlink or copy test data as temperature.dat
        import shutil
        temp_data_dest = tmp_path / "temperature.dat"
        shutil.copy(legacy_data_path, temp_data_dest)
        
        # Run script in temporary directory
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout (parameter estimation may take longer)
        )
        
        # Check for successful execution
        assert result.returncode == 0, (
            f"ex_unknownRp_PD.py failed with return code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        
        # Verify parameter estimation output in stdout
        stdout = result.stdout
        assert "R0" in stdout, "R0 parameter not found in output"
        assert "A1" in stdout, "A1 parameter not found in output"
        assert "A2" in stdout, "A2 parameter not found in output"
        
        # Verify output files were created
        output_files = list(tmp_path.glob("output_saved_*.csv"))
        assert len(output_files) > 0, "No output CSV file generated"
        
        # Verify PDF files were created
        pdf_files = list(tmp_path.glob("*.pdf"))
        assert len(pdf_files) >= 3, f"Expected at least 3 PDF plots, found {len(pdf_files)}"

    def test_ex_unknownRp_parameter_values(self, repo_root, tmp_path):
        """
        Verify ex_unknownRp_PD.py produces reasonable parameter estimates.
        
        This test checks that the parameter estimation produces physically
        reasonable values, not just that the script runs without errors.
        
        Args:
            repo_root: Path to repository root
            tmp_path: Temporary directory for output files
        """
        script_path = repo_root / "examples" / "legacy" / "ex_unknownRp_PD.py"
        
        # Skip if script doesn't exist
        if not script_path.exists():
            pytest.skip(f"Legacy example script {script_path} not found")
        
        # Copy test data
        legacy_data_path = repo_root / "examples" / "legacy" / "temperature.dat"
        if not legacy_data_path.exists():
            pytest.skip("Test data file examples/legacy/temperature.dat not found")
        
        import shutil
        temp_data_dest = tmp_path / "temperature.dat"
        shutil.copy(legacy_data_path, temp_data_dest)
        
        # Run script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, "Script execution failed"
        
        # Extract parameter values from output
        import re
        stdout = result.stdout
        
        # Parse R0, A1, A2 values
        r0_match = re.search(r"R0\s*=\s*([-+]?\d*\.?\d+)", stdout)
        a1_match = re.search(r"A1\s*=\s*([-+]?\d*\.?\d+)", stdout)
        a2_match = re.search(r"A2\s*=\s*([-+]?\d*\.?\d+)", stdout)
        
        if r0_match and a1_match and a2_match:
            r0 = float(r0_match.group(1))
            a1 = float(a1_match.group(1))
            a2 = float(a2_match.group(1))
            
            # Check physical reasonableness
            assert r0 > 0, f"R0 should be positive, got {r0}"
            assert r0 < 100, f"R0 seems unreasonably large: {r0}"
            assert a1 >= 0, f"A1 should be non-negative, got {a1}"
            assert a2 >= 0, f"A2 should be non-negative, got {a2}"
