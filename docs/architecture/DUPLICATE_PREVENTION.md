# Duplicate Prevention Feature

**Date:** December 16, 2025  
**Feature:** Skip logging similar bugs (>90% similarity)  
**Status:** ✅ COMPLETE

---

## Summary

The system now prevents logging duplicate bugs to keep the history clean and reduce storage. When a bug has >90% similarity to an existing logged bug, it's considered a duplicate and not re-logged.

---

## How It Works

### Before (Previous Behavior)
```
Every bug analyzed → Always logged to history
Problem: Duplicate bugs create redundant entries
```

### After (New Behavior)
```
Bug analyzed → Check similarity to existing bugs
  ├─ If highest similarity > 90% → Skip logging (duplicate)
  └─ If highest similarity ≤ 90% → Log to history (unique)
```

---

## Implementation

### Modified: `src/main.py`

**In `run()` method (batch analysis):**
```python
# Check if this is a duplicate (>90% similarity to existing bug)
if similar_bugs and len(similar_bugs) > 0:
    highest_similarity = similar_bugs[0].get('score', 0)
    if highest_similarity > 0.90:
        print(f"  ⚠ Skipping log: Bug is {highest_similarity:.1%} similar to {similar_bugs[0].get('bug', {}).get('key')} (likely duplicate)")
    else:
        # Log to history
        ...
```

**In `analyze_single_bug()` method:**
```python
# Check if this is a duplicate (>90% similarity to existing bug)
should_log = True
if 'similar_bugs' in locals() and similar_bugs and len(similar_bugs) > 0:
    highest_similarity = similar_bugs[0].get('score', 0)
    if highest_similarity > 0.90:
        print(f"\n⚠ Skipping log: Bug is {highest_similarity:.1%} similar to {similar_bugs[0].get('bug', {}).get('key')} (likely duplicate)")
        should_log = False

if should_log:
    # Log to history
    ...
```

---

## Console Output Examples

### Unique Bug (Logged)
```
🔍 Searching log history for similar bugs...
✓ Found 2 similar bug(s) in history
✓ Analysis logged to history
```

### Duplicate Bug (Not Logged)
```
🔍 Searching log history for similar bugs...
✓ Found 1 similar bug(s) in history
⚠ Skipping log: Bug is 95.3% similar to ABC-123 (likely duplicate)
```

### New Bug (No History)
```
🔍 Searching log history for similar bugs...
ℹ No similar bugs found in history
✓ Analysis logged to history
```

---

## Similarity Thresholds

```
 0%            70%           80%           90%         100%
 ├─────────────┼─────────────┼─────────────┼─────────────┤
               │             │             │
        Context Threshold   Good Ref   Duplicate Threshold
        (Include in prompt) (Strong)   (Don't log)
```

| Score | Behavior |
|-------|----------|
| < 70% | No context provided, bug is logged |
| 70-90% | Context provided, bug is logged |
| > 90% | Context provided, **bug NOT logged** (duplicate) |

---

## Benefits

### 1. Clean Log History ✅
- No duplicate entries
- Easier to browse and analyze
- Better data quality

### 2. Reduced Storage ✅
- Fewer documents in OpenSearch
- Lower storage costs
- Faster queries

### 3. Better Analytics ✅
- Accurate count of unique issues
- Easier to identify patterns
- No inflated metrics

### 4. Still Provides Context ✅
- Duplicate bugs still get historical context
- Analysis proceeds normally
- Only logging step is skipped

---

## Edge Cases Handled

### 1. No Similar Bugs Found
```python
if similar_bugs and len(similar_bugs) > 0:
    # Check similarity
else:
    # Log anyway (new unique bug)
```

### 2. Similar But Not Duplicate (70-90%)
```python
if highest_similarity > 0.90:
    # Skip logging
else:
    # Log it (different enough to be unique)
```

### 3. Log History Disabled
```python
if self.log_history:
    # Check and log
# If disabled, no checking occurs
```

---

## Testing

### Manual Test
1. Analyze a bug (gets logged)
2. Analyze the same or very similar bug again
3. Should see: "⚠ Skipping log: Bug is X% similar to Y (likely duplicate)"

### Verification
```bash
# Run analysis
python main.py

# Check OpenSearch for duplicate entries
curl -X GET "http://localhost:9200/bug_analysis_logs/_search?q=bug_key:ABC-123"

# Should only see one entry per unique bug
```

---

## Configuration

### Duplicate Threshold (hardcoded in main.py)
```python
if highest_similarity > 0.90:  # 90% threshold
```

**To adjust:**
- **0.85** - More strict, fewer duplicates detected
- **0.90** - Balanced (current default)
- **0.95** - More lenient, only exact duplicates skipped

### Context Threshold (already configurable)
```python
similar_bugs = self.log_history.search_similar_bugs(
    query=f"{bug.summary} {bug.description or ''}",
    limit=3,
    min_score=0.7  # Context threshold
)
```

---

## Updated Documentation

- ✅ [docs/CONTEXTUAL_ANALYSIS.md](docs/CONTEXTUAL_ANALYSIS.md) - Added duplicate prevention section
- ✅ [docs/CONTEXTUAL_ANALYSIS_FLOW.md](docs/CONTEXTUAL_ANALYSIS_FLOW.md) - Updated flow diagram
- ✅ This document - Complete feature description

---

## Real-World Example

### Scenario: Same Bug Reported Twice

**First Analysis (ABC-123):**
```
Summary: "Login fails with NullPointerException"
🔍 Searching log history for similar bugs...
ℹ No similar bugs found in history
✓ Analysis logged to history
```

**Second Analysis (ABC-456) - Same Issue:**
```
Summary: "NPE when logging in"
🔍 Searching log history for similar bugs...
✓ Found 1 similar bug(s) in history
⚠ Skipping log: Bug is 94.2% similar to ABC-123 (likely duplicate)

Claude still receives context from ABC-123!
Analysis proceeds normally.
Report generated.
```

**Result:**
- ✅ ABC-456 gets analyzed with context from ABC-123
- ✅ Only ABC-123 is in log history (no duplicate)
- ✅ Storage saved, history clean
- ✅ Both bugs get proper analysis

---

## Important Notes

1. **Analysis Still Happens**: Duplicate detection only affects logging, not analysis
2. **Context Still Provided**: Duplicate bugs still receive historical context
3. **Reports Still Generated**: All bugs get reports regardless of logging
4. **Jira Still Updated**: (if configured) Bug status updates work normally

The only thing skipped is adding a duplicate entry to OpenSearch.

---

## Future Enhancements

Potential improvements:
- [ ] Make threshold configurable in `.env`
- [ ] Add "duplicate_of" reference in bug metadata
- [ ] Link duplicate bugs to original in reports
- [ ] Track duplicate count for analytics
- [ ] Auto-close duplicates in Jira (optional)

---

**Feature Status:** ✅ Production Ready  
**Impact:** Positive - Cleaner data, reduced storage, same analysis quality
