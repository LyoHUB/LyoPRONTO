# CI Workflow Guide

## Overview

The LyoPRONTO project uses a **smart, draft-aware CI workflow** for optimal developer experience and quality assurance:

1. **Draft PRs**: Fast tests only (3-5 minutes) - rapid iteration
2. **Ready for Review**: Full coverage (5-7 minutes) - quality verification
3. **Main Branch**: Full coverage (5-7 minutes) - maintain metrics

This approach provides quick feedback during development while ensuring thorough quality checks when PR is ready for review.

## Workflow Stages

### Stage 1: Development & Review (Fast Tests)

**Workflow**: `.github/workflows/pr-tests.yml`

**Triggers**: Every commit pushed to a pull request
- PR opened
- New commits pushed (synchronize)
- PR reopened

**What runs**:
```bash
pytest tests/ -n auto -v  # No coverage
```

**Duration**: ~3-5 minutes

**Purpose**:
- ✅ Quick feedback for developers
- ✅ Catch breaking changes immediately
- ✅ Allow rapid iteration
- ❌ No coverage analysis (saves ~2 minutes)

**When it runs**:
```
Developer pushes code → Fast tests run automatically
↓
Tests pass → Ready for review
Tests fail → Developer fixes and pushes again → Fast tests re-run
```

### Stage 2: Pre-Merge Verification (Full Coverage)

**Workflow**: `.github/workflows/tests.yml`

**Triggers**: 
1. PR approved by reviewer
2. Direct pushes to `main` or `dev-pyomo` branches

**What runs**:
```bash
pytest tests/ -n auto -v --cov=lyopronto --cov-report=xml
# + Upload to Codecov
```

**Duration**: ~5-7 minutes

**Purpose**:
- ✅ Full quality verification before merge
- ✅ Coverage analysis and reporting
- ✅ Final confirmation PR is merge-ready
- ✅ Maintain quality metrics on main branch

**When it runs**:
```
Developer pushes code → Fast tests pass → Reviewer approves PR
↓
Full coverage tests run automatically
↓
Coverage tests pass → Safe to merge
Coverage tests fail → Address issues before merge
```

## Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Pull Request Lifecycle                    │
└─────────────────────────────────────────────────────────────┘

1. Developer Creates PR
   └─> Fast Tests Run (pr-tests.yml)
       ├─ Duration: ~3-5 min
       ├─ No coverage
       └─ Result: ✅ or ❌

2. Developer Pushes More Commits
   └─> Fast Tests Re-run (pr-tests.yml)
       └─ Every commit triggers new run

3. Reviewer Approves PR
   └─> Full Coverage Tests Run (tests.yml)
       ├─ Duration: ~5-7 min
       ├─ With coverage
       ├─ Upload to Codecov
       └─ Result: ✅ or ❌

4. Merge to Main
   └─> Full Coverage Tests Run Again (tests.yml)
       └─> Updates coverage metrics for main branch
```

## GitHub Actions Triggers

### PR Tests (Fast)
```yaml
on:
  pull_request:
    branches: [ main, dev-pyomo ]
    types: [ opened, synchronize, reopened ]
```

### Coverage Tests (Full)
```yaml
on:
  push:
    branches: [ main, dev-pyomo ]
  pull_request_review:
    types: [ submitted ]

jobs:
  test:
    if: |
      github.event_name == 'push' || 
      (github.event_name == 'pull_request_review' && github.event.review.state == 'approved')
```

## Benefits of This Approach

### For Developers
- ⚡ **Fast feedback** (3-5 min instead of 11+ min)
- 🔄 **Quick iterations** during development
- 🎯 **Focus on functionality** first, coverage later
- 💰 **Saves CI minutes** (reduced by 55-73% per commit)

### For Reviewers
- ✅ **Immediate test status** when reviewing code
- 📊 **Full coverage** before approving merge
- 🔒 **Quality gate** at approval time
- 🚦 **Clear merge readiness** signals

### For Project Maintainers
- 📈 **Maintain high coverage** on main branch
- 💸 **Reduce CI costs** (fewer coverage runs)
- ⚙️ **Optimize resource usage**
- 📊 **Accurate coverage metrics** for merged code

## Comparison with Other Strategies

| Strategy | PR Commits | After Approval | Total CI Time | Pros | Cons |
|----------|------------|----------------|---------------|------|------|
| **Our Approach** | Fast (3-5m) | Full (5-7m) | **8-12m total** | ✅ Fast iteration<br>✅ Full verification | Requires approval workflow |
| Run coverage every time | Full (11m) | - | **11m × commits** | Simple setup | ❌ Slow feedback<br>❌ Expensive |
| No coverage on PRs | Fast (3-5m) | - | **3-5m total** | ✅ Very fast | ❌ No coverage check |
| Coverage on merge only | - | Full (5-7m) | **5-7m** | Minimal runs | ❌ Late discovery |

## Example Timeline

### Scenario: PR with 3 commits before approval

**Before optimization** (coverage on every commit):
```
Commit 1: 11 min
Commit 2: 11 min  
Commit 3: 11 min
Approval: -
Merge:    11 min
────────────────
Total:    44 minutes
```

**After optimization** (our approach):
```
Commit 1: 3 min (fast)
Commit 2: 3 min (fast)
Commit 3: 3 min (fast)
Approval: 7 min (full coverage)
Merge:    7 min (full coverage)
────────────────
Total:    23 minutes (47% reduction! 🎉)
```

## Monitoring & Troubleshooting

### Check Workflow Status

In GitHub UI:
1. Go to "Actions" tab
2. See "PR Tests (Fast)" for development feedback
3. See "Tests (with Coverage)" after approval/merge

### If Fast Tests Fail
- Fix the code
- Push new commit
- Fast tests re-run automatically

### If Coverage Tests Fail After Approval
- Review coverage report
- Add missing tests
- Push new commit
- Fast tests run again
- Request re-approval
- Coverage tests run again

### Expected Behavior

| Event | Fast Tests | Coverage Tests |
|-------|------------|----------------|
| Open PR | ✅ Run | ❌ Skip |
| Push to PR | ✅ Run | ❌ Skip |
| Request changes | ✅ Continue | ❌ Skip |
| Approve PR | ✅ Already ran | ✅ Run |
| Merge to main | ❌ Skip | ✅ Run |

## Manual Override (If Needed)

To manually trigger full coverage tests without approval:

1. Go to Actions tab
2. Select "Tests (with Coverage)" workflow
3. Click "Run workflow"
4. Select branch

Or add a comment to trigger (if you set up comment triggers):
```
/run-coverage
```

## Configuration Files

- `.github/workflows/pr-tests.yml` - Fast tests for PRs
- `.github/workflows/tests.yml` - Full coverage tests
- `pytest.ini` - Test configuration
- `.coveragerc` - Coverage configuration (if present)

## Best Practices

### For Contributors
1. ✅ Run tests locally before pushing: `pytest tests/ -n auto`
2. ✅ Push small, focused commits
3. ✅ Wait for fast tests to pass before requesting review
4. ✅ Address any coverage gaps when requested

### For Reviewers
1. ✅ Check that fast tests passed
2. ✅ Review code quality and logic
3. ✅ Approve when ready to trigger full coverage
4. ✅ Wait for coverage tests to pass before merging

### For Maintainers
1. ✅ Monitor CI run times in Actions tab
2. ✅ Review coverage trends in Codecov
3. ✅ Adjust coverage thresholds as needed
4. ✅ Update workflows if patterns change

## Troubleshooting

### "Coverage tests didn't run after approval"

**Possible causes**:
1. Review was "Comment" or "Request changes" (not "Approve")
2. Workflow condition may need adjustment
3. Check Actions tab for workflow status

**Solution**: 
- Ensure reviewer clicked "Approve" (not just comment)
- Check workflow logs for condition evaluation

### "Fast tests taking too long"

**Expected**: 3-5 minutes  
**Investigate if**: >7 minutes

**Possible causes**:
1. Package installation not cached
2. Too many tests running
3. GitHub runner performance issues

**Solution**:
- Check cache hit rate in workflow logs
- Consider test sharding if >200 tests
- Report if consistently slow

### "Coverage decreased after merge"

**This is expected** during development.

**Actions**:
1. Review uncovered lines in Codecov
2. Add tests in follow-up PR
3. Set coverage thresholds in `.coveragerc`

## Future Enhancements

Potential improvements to consider:

1. **Test Sharding** - Split tests across parallel jobs for >200 tests
2. **Selective Testing** - Only run tests for changed modules
3. **Comment Triggers** - Manual `/run-coverage` command
4. **Draft PR Handling** - Skip CI for draft PRs
5. **Coverage Diff** - Show coverage change in PR comments

## References

- [GitHub Actions: Workflow triggers](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)
- [pull_request_review event](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request_review)
- [pytest-xdist](https://pytest-xdist.readthedocs.io/) - Parallel testing
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin
- [Codecov](https://about.codecov.io/) - Coverage reporting
