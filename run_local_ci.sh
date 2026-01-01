#!/bin/bash
# Local CI simulation script
# This script replicates the GitHub Actions CI environment locally

set -e  # Exit on error

echo "=========================================="
echo "LyoPRONTO Local CI Simulation"
echo "=========================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | grep -oP '\d+\.\d+')
echo "   Current Python: $(python --version)"
if [[ "$PYTHON_VERSION" != "3.13" ]]; then
    echo "   ⚠️  Warning: CI uses Python 3.13, you have $PYTHON_VERSION"
    echo "   Consider using: conda create -n LyoPRONTO python=3.13"
fi
echo ""

# Check if we're in the right directory
echo "2. Checking repository structure..."
if [ ! -f "pytest.ini" ] || [ ! -d "tests" ] || [ ! -d "lyopronto" ]; then
    echo "   ❌ Error: Must run from repository root"
    exit 1
fi
echo "   ✅ Repository structure OK"
echo ""

# Install/update dependencies
echo "3. Installing dependencies..."
echo "   Upgrading pip..."
python -m pip install --upgrade pip -q
echo "   Installing core dependencies..."
pip install . -q
echo "   Installing dev dependencies..."
pip install .[dev] -q
echo "   ✅ Dependencies installed"
echo ""

# Run tests with coverage (matching CI)
echo "4. Running test suite (matching CI configuration)..."
echo "   Using parallel execution with 8 workers (optimal for this system)..."
echo "   Command: pytest tests/ -n 8 -v --cov=lyopronto --cov-report=xml --cov-report=term-missing"
echo ""
pytest tests/ -n 8 -v --cov=lyopronto --cov-report=xml --cov-report=term-missing

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ All tests passed!"
    echo "=========================================="
    echo ""
    echo "Coverage report saved to: coverage.xml"
    echo "You can view detailed coverage with: coverage html && open htmlcov/index.html"
    echo ""
    echo "Note: Tests run in parallel for speed. For debugging, use: pytest tests/ -v"
    echo "This matches the CI environment. You're ready to push!"
else
    echo ""
    echo "=========================================="
    echo "❌ Tests failed!"
    echo "=========================================="
    echo ""
    echo "Fix the failing tests before pushing to trigger CI."
    exit 1
fi
