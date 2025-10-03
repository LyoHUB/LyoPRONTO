# CI Workflow Recommendation & Comparison

## Executive Summary

**Recommended Approach**: **Draft-Aware CI Workflow** ✅

This strikes the best balance between developer experience, cost efficiency, and quality assurance.

## The Problem

Original CI: **11 minutes** per run (too slow for 128 tests)

## Solution Comparison

### Option 1: Full Tests Every Time (Industry Standard)
```yaml
Every commit → Full tests + coverage (5-7 min)
```

**Scoring**:
- Developer Experience: ⭐⭐⭐⭐ (4/5)
- Quality Assurance: ⭐⭐⭐⭐⭐ (5/5)
- Cost Efficiency: ⭐⭐⭐ (3/5)
- Complexity: ⭐⭐⭐⭐⭐ (5/5 - simplest)

**Best for**: Projects with strict quality requirements, unlimited CI budget

**Example**:
```
Commit 1: 7 min with coverage
Commit 2: 7 min with coverage
Commit 3: 7 min with coverage
Total: 21 minutes
```

---

### Option 2: Parallel Fast + Full (Modern)
```yaml
Every commit → Fast tests (3 min) AND Coverage tests (7 min) in parallel
```

**Scoring**:
- Developer Experience: ⭐⭐⭐⭐⭐ (5/5)
- Quality Assurance: ⭐⭐⭐⭐⭐ (5/5)
- Cost Efficiency: ⭐⭐ (2/5 - highest cost)
- Complexity: ⭐⭐⭐ (3/5)

**Best for**: Critical infrastructure projects, large teams

**Example**:
```
Commit 1: 7 min (both run in parallel)
Commit 2: 7 min (both run in parallel)
Commit 3: 7 min (both run in parallel)
Total: 21 minutes (but you see fast results in 3 min)
```

---

### Option 3: Approval-Based Coverage (Your Original Idea)
```yaml
PR commits → Fast tests only (3 min)
Reviewer approval → Coverage tests (7 min)
```

**Scoring**:
- Developer Experience: ⭐⭐⭐⭐ (4/5)
- Quality Assurance: ⭐⭐⭐ (3/5 - late discovery)
- Cost Efficiency: ⭐⭐⭐⭐⭐ (5/5 - lowest cost)
- Complexity: ⭐⭐⭐ (3/5)

**Best for**: Budget-constrained projects, small teams

**Issues**:
- ⚠️ Coverage gaps discovered AFTER reviewer approves
- ⚠️ Rework required → new approval → rework loop
- ⚠️ Reviewer frustration ("I already approved this!")
- ⚠️ Violates "shift left" testing principle

**Example**:
```
Commit 1: 3 min fast
Commit 2: 3 min fast
Commit 3: 3 min fast
Reviewer approves: 7 min coverage → FAILS!
Fix & recommit: 3 min fast
Re-approval needed: 7 min coverage
Total: 26 minutes + approval friction
```

---

### Option 4: Draft-Aware CI (RECOMMENDED ⭐)
```yaml
Draft PR commits → Fast tests only (3 min)
Mark "Ready for Review" → Full tests + coverage (7 min)
All subsequent commits → Full tests + coverage (7 min)
```

**Scoring**:
- Developer Experience: ⭐⭐⭐⭐⭐ (5/5)
- Quality Assurance: ⭐⭐⭐⭐⭐ (5/5)
- Cost Efficiency: ⭐⭐⭐⭐ (4/5)
- Complexity: ⭐⭐⭐⭐ (4/5)

**Best for**: Most projects - excellent balance ✅

**Advantages**:
- ✅ Fast iteration during development (draft)
- ✅ Full coverage BEFORE review (ready)
- ✅ No post-approval surprises
- ✅ Natural developer workflow
- ✅ Significant cost savings during development

**Example**:
```
Draft Commit 1: 3 min fast
Draft Commit 2: 3 min fast
Draft Commit 3: 3 min fast
Mark "Ready for Review": 7 min coverage
Review feedback commit: 7 min coverage
Total: 23 minutes + no approval friction ✅
```

---

## Detailed Comparison Table

| Aspect | Option 1<br>(Always Full) | Option 2<br>(Parallel) | Option 3<br>(Approval) | Option 4<br>(Draft-Aware) ✅ |
|--------|----------------|------------|-------------|-------------------|
| **Development Speed** | Slower (7 min) | Fast (3 min visible) | Fast (3 min) | Fast (3 min draft) |
| **Review Readiness** | Excellent | Excellent | Unknown | Excellent |
| **Coverage Discovery** | Immediate | Immediate | Late (post-approval) | Early (pre-review) |
| **CI Cost (3 commits)** | 21 min | 42 min | 16 min | 23 min |
| **Rework Risk** | Low | Low | **High** ⚠️ | Low |
| **Setup Complexity** | Simple | Moderate | Moderate | Moderate |
| **Reviewer Experience** | Good | Good | **Frustrating** ⚠️ | Excellent |
| **Industry Standard** | ✅ Yes | Used by large projects | ❌ Uncommon | Growing adoption |

---

## Real-World Scenarios

### Scenario A: Developer making quick fix
**Draft-Aware (Recommended)**:
```
1. Create draft PR → 3 min fast test ✅
2. Push fix → 3 min fast test ✅
3. Mark ready → 7 min with coverage ✅
Total: 13 minutes, ready for review
```

**Approval-Based**:
```
1. Create PR → 3 min fast test ✅
2. Push fix → 3 min fast test ✅
3. Reviewer approves → 7 min coverage → FAILS! ❌
4. Fix coverage → 3 min fast test
5. Get re-approval → 7 min coverage ✅
Total: 23 minutes + approval hassle
```

### Scenario B: Developer iterating on feature (5 commits)
**Draft-Aware (Recommended)**:
```
Draft commits 1-4: 3 min each = 12 min
Mark ready: 7 min
Review fix: 7 min
Total: 26 minutes
```

**Always Full**:
```
All 5 commits: 7 min each = 35 minutes
Total: 35 minutes (34% slower)
```

**Approval-Based**:
```
Commits 1-5: 3 min each = 15 min
Approval → coverage fails: 7 min
Fix + re-approval: 10 min
Total: 32 minutes + frustration
```

---

## Why Draft-Aware is Better Than Approval-Based

### The Approval Problem

**Approval-Based workflow**:
```
Developer: "I'm done, please review"
   ↓
Reviewer: "Code looks good!" → Clicks approve
   ↓
CI: "Coverage dropped, tests fail"
   ↓
Reviewer: "Wait, I need to re-approve?"
Developer: "Sorry, let me fix..."
   ↓
[Repeat cycle]
```

**Draft-Aware workflow**:
```
Developer: "I'm working on this" → Draft
   [Fast iterations]
   ↓
Developer: "Done! Ready for review" → Mark ready
   ↓
CI: Runs full coverage immediately
   ↓
If pass: Reviewer sees "all green"
If fail: Developer fixes BEFORE review
   ↓
Reviewer: Gets clean, verified PR to review
```

### Key Insights

1. **Approval is a social contract** - "I think this is good to merge"
   - Breaking this after approval damages trust
   - Requires awkward "sorry, need re-approval" conversations

2. **"Ready for Review" is a technical signal** - "This is complete"
   - Perfect trigger for full quality checks
   - Natural part of developer workflow
   - No social friction if CI fails

3. **Shift left principle** - Find issues as early as possible
   - Draft-aware: Issues found before review ✅
   - Approval-based: Issues found after approval ❌

---

## Implementation: Draft-Aware Workflow

### How It Works

```yaml
# .github/workflows/pr-tests.yml

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review, converted_to_draft]

jobs:
  test:
    steps:
    - name: Determine mode
      run: |
        if [ "${{ github.event.pull_request.draft }}" == "true" ]; then
          echo "mode=fast" 
        else
          echo "mode=full"
        fi
    
    - name: Run tests
      run: |
        if [ "$mode" == "fast" ]; then
          pytest tests/ -n auto -v  # 3-5 min
        else
          pytest tests/ -n auto -v --cov=lyopronto  # 5-7 min
        fi
```

### Developer Workflow

```bash
# 1. Start development
git checkout -b feature/my-feature
git push -u origin feature/my-feature

# 2. Create DRAFT PR
gh pr create --draft --title "WIP: My feature"
# → Fast tests run (3 min)

# 3. Iterate quickly
git commit -am "Progress"
git push
# → Fast tests run (3 min each)

# 4. When done, mark ready
gh pr ready
# → Full coverage tests run automatically (7 min)

# 5. If coverage passes, request review
gh pr ready  # already done
# → Reviewer sees all-green PR ✅

# 6. If coverage fails, fix before review
git commit -am "Add tests"
git push
# → Full coverage runs again (7 min)
```

---

## Adoption Path

### Phase 1: Implement Draft-Aware (Recommended Now)
```
Week 1: Deploy draft-aware workflow
Week 2-4: Team adapts to using draft PRs
Result: 30-40% CI time reduction
```

### Phase 2: Monitor & Optimize (Month 2)
```
Track:
- Average draft commits per PR
- Coverage failure rate
- Developer satisfaction
```

### Phase 3: Consider Parallel (If Needed)
```
If budget allows and team is large:
- Add parallel fast+full tests
- Keep draft awareness for cost control
```

---

## Recommendations by Project Size

### Small Team (1-5 developers)
**Use**: Draft-Aware Workflow ✅
- Best balance of speed and quality
- Low complexity
- Significant cost savings

### Medium Team (6-20 developers)
**Use**: Draft-Aware Workflow ✅
- Consider parallel tests if CI budget allows
- Strong quality gates needed

### Large Team (20+ developers)
**Use**: Parallel Fast+Full
- Budget for comprehensive CI
- Many concurrent PRs
- Critical quality requirements

---

## Cost Analysis (100 PRs/month)

Assumptions:
- Average 4 commits per PR
- 1 review cycle per PR

| Workflow | Minutes/PR | Total/Month | Relative Cost |
|----------|------------|-------------|---------------|
| Always Full (7 min) | 35 min | 3,500 min | 100% baseline |
| Parallel (7 min × 2) | 70 min | 7,000 min | 200% (+$$$) |
| Approval-Based (best case) | 19 min | 1,900 min | 54% (−$$) |
| Approval-Based (with rework) | 29 min | 2,900 min | 83% |
| **Draft-Aware** ✅ | **26 min** | **2,600 min** | **74%** (−$) |

**Draft-Aware saves 26% vs Always Full** while maintaining quality ✅

---

## Conclusion

### Why Draft-Aware Wins

1. ✅ **Fast iteration** during development (like approval-based)
2. ✅ **Full coverage** before review (like always-full)
3. ✅ **No approval friction** (unlike approval-based)
4. ✅ **Cost efficient** (better than always-full)
5. ✅ **Natural workflow** (developers already use drafts)
6. ✅ **Early problem detection** ("shift left")
7. ✅ **Reviewer-friendly** (always see verified PRs)

### Implementation Verdict

**Switch from approval-based to draft-aware** for:
- Better developer experience
- No reviewer friction
- Earlier problem detection
- Same cost efficiency
- Industry-aligned workflow

The approval-based approach is clever but creates social friction. Draft-aware achieves the same goals without the downsides.

---

## Further Reading

- [GitHub: Draft Pull Requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests)
- [Shift Left Testing](https://en.wikipedia.org/wiki/Shift-left_testing)
- [The Cost of Late Discovery](https://www.researchgate.net/publication/255965523_Evaluating_the_cost_of_software_quality)
- [GitHub Actions: Pull Request Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request)
