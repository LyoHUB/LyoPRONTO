#!/bin/bash
# Local CI simulation script
# This script replicates the GitHub Actions CI environment locally

echo "=========================================="
echo "LyoPRONTO Local CI Simulation"
echo "=========================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "   Current Python: $(python --version)"
if [[ "$PYTHON_VERSION" != "3.13" ]]; then
    echo "   Warning: CI uses Python 3.13, you have $PYTHON_VERSION"
    echo "   Consider using: conda create -n LyoPRONTO python=3.13"
fi
echo ""

# Check if we're in the right directory
echo "2. Checking repository structure..."
if [ ! -f "pytest.ini" ] || [ ! -d "tests" ] || [ ! -d "lyopronto" ]; then
    echo "   Error: Must run from repository root"
    exit 1
fi
echo "   Repository structure OK"
echo ""

# Install/update dependencies
echo "3. Installing dependencies..."
echo "   Upgrading pip..."
python -m pip install --upgrade pip -q
echo "   Installing package with dev dependencies..."
pip install -e ".[dev]" -q
echo "   Dependencies installed"
echo ""

# Run tests with coverage (matching CI)
echo "4. Running test suite (matching CI configuration)..."
echo "   Command: pytest tests/ -v --cov=lyopronto --cov-report=xml --cov-report=term-missing"
echo ""
if pytest tests/ -v --cov=lyopronto --cov-report=xml --cov-report=term-missing; then
    echo ""
    echo "=========================================="
    echo "All tests passed!"
    echo "=========================================="
    echo ""
    echo "Coverage report saved to: coverage.xml"
    echo "You can view detailed coverage with: coverage html && open htmlcov/index.html"
    echo ""
    echo "Note: Tests run in parallel for speed. For debugging, use: pytest tests/ -v -n 0"
    echo "This matches the CI environment. You're ready to push!"
else
    echo ""
    echo "=========================================="
    echo "Tests failed!"
    echo "=========================================="
    echo ""
    echo "Fix the failing tests before pushing to trigger CI."
    exit 1
fi
