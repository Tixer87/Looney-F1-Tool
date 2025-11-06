# RLT Adapter - Regression Guard & Validation

**Status**: ✅ Active  
**Coverage Target**: 92% for `export/` + `mapping/`  
**Golden Fixture**: Mexico 2025 Qualification

---

## Quick Start

### 1. Run Validation Guard (Fast)

```bash
# Validate any qualification export
python tools/validate_rlt_quali.py path/to/quali_export.json
```

**Expected Output**:
```
✅ RLT Quali schema: OK
```

### 2. Run Golden Fixture Tests

```bash
# Run qualification schema regression tests
pytest tests/test_quali_schema.py -v
```

**Expected**: 23/23 PASS

### 3. Run Full Test Suite with Coverage

```bash
# All tests with coverage report
pytest tests/ --cov=export --cov=mapping --cov-fail-under=92
```

---

## Validation Guard: `tools/validate_rlt_quali.py`

### Purpose
Fast schema validation for qualification exports. Checks:
- ✅ All required top-level fields present (18 fields)
- ✅ FastestLapDriver object structure
- ✅ Q1 field MANDATORY for all drivers
- ✅ Q1 format "m:ss.mmm" valid
- ✅ Status="Ok" for all drivers

### Usage

**Validate Single File**:
```bash
python tools/validate_rlt_quali.py mexico_2025_quali.json
```

**Integrate in Export Script**:
```python
import subprocess
result = subprocess.run(
    ["python", "tools/validate_rlt_quali.py", output_path],
    capture_output=True
)
if result.returncode != 0:
    raise ValueError("Qualification export validation failed")
```

**Exit Codes**:
- `0` = Valid
- `1` = Validation failed

---

## Golden Fixture Tests: `tests/test_quali_schema.py`

### Purpose
Regression tests against golden qualification fixture (Mexico 2025). Prevents:
- Missing required fields
- Wrong Status values
- Missing Q1 times
- "Unknown" entries in teams/nationalities

### Test Coverage

**23 Tests**:
1. ✅ Top-level required fields (18 fields)
2. ✅ SessionType = "Qualification"
3. ✅ QualType field exists
4. ✅ FastestLapDriver object structure
5. ✅ Drivers list not empty
6. ✅ Driver required fields (11 fields)
7. ✅ Q1 field MANDATORY for all drivers
8. ✅ Q1 format valid ("m:ss.mmm")
9. ✅ Status="Ok" for all drivers
10. ✅ Driver/Team nested objects
11. ✅ Zero "Unknown Team" entries
12. ✅ Zero "Unknown" nationality entries
13. ✅ TimeInt populated (not 0)
14. ✅ Gap calculation (P1 has GapInt=0)
15-23. ✅ Field type validation (9 parametrized tests)

### Golden Fixture

**File**: `tests/fixtures/mexico_2025_quali.json`  
**Source**: Mexico 2025 Qualification (Round 20)  
**Drivers**: 2 (Lando Norris, Charles Leclerc)  
**Status**: ✅ Validated against Admin-Spec

**Update Golden Fixture**:
```bash
# Re-export and copy as new golden fixture
python ft_mexico_export.py
cp release/v1.7/fieldtest_mexico/20251101_2130/raw/mexico_2025_quali.json \
   tests/fixtures/mexico_2025_quali.json
```

---

## Integration with Field Test

The `ft_mexico_export.py` script now **automatically validates** qualification exports:

```python
# Export Qualifying
quali_ok, quali_path = export_mexico_session("quali", output_path)

# Validate automatically
if quali_ok:
    validate_quali_export(quali_path)  # Calls validator tool
```

**Output**:
```
1. Exporting Qualifying...
[OK] Exported quali to: mexico_2025_quali.json

   → Running schema validation...
   ✅ Top-level fields: 18/18 present
   ✅ FastestLapDriver: Lando Norris (United Kingdom)
   ✅ Drivers: 20 total
   ✅ All 20 drivers: Status='Ok', Q1 format valid
   
   ✅ RLT Quali schema: OK
```

---

## Coverage Requirements

### Target: 92%

**Measured Modules**:
- `export/rlt_adapter.py` (401 statements)
- `export/rlt_enums.py` (14 statements)
- `mapping/teams_aliases.py` (70 statements)
- `mapping/drivers_aliases.py` (79 statements)
- `mapping/drivers_nations.py` (64 statements)
- `mapping/circuit_aliases.py` (88 statements)

**Total**: 759 statements

### Run Coverage Report

```bash
# HTML report
pytest tests/ --cov=export --cov=mapping --cov-report=html
# Open htmlcov/index.html

# Terminal report
pytest tests/ --cov=export --cov=mapping --cov-report=term-missing
```

**Note**: Golden fixture tests (`test_quali_schema.py`) are marked `@pytest.mark.golden` and don't contribute to coverage (they only validate JSON structure).

---

## Zero-Unknowns Gate

### Phase C++ H1 Requirement

**Zero "Unknown" entries** in all exports:
- ❌ "Unknown Team"
- ❌ "Unknown Nationality"

### Validation

**In Validator** (`tools/validate_rlt_quali.py`):
```python
# Implicit: Teams/nationalities already validated by mapping in adapter
# No explicit check needed (would fail earlier in build_rlt_session)
```

**In Pytest** (`tests/test_quali_schema.py`):
```python
def test_quali_zero_unknown_teams(golden_quali):
    """Test that no drivers have 'Unknown Team'."""
    # Searches for "Unknown" in Team.Name fields
    
def test_quali_zero_unknown_nationalities(golden_quali):
    """Test that no drivers have 'Unknown' nationality."""
    # Searches for "Unknown"/"UNK" in Driver.Nationality fields
```

---

## Success Criteria

### ✅ All Gates Pass

1. **Validator**: `python tools/validate_rlt_quali.py quali.json` → Exit 0
2. **Pytest**: `pytest tests/test_quali_schema.py` → 23/23 PASS
3. **Coverage**: `pytest tests/ --cov --cov-fail-under=92` → ≥92%
4. **RLT Import**: Load export in RLT application → No errors

---

## Troubleshooting

### Validator Fails

```
❌ Driver 5 (Lewis Hamilton) missing Q1 field (MANDATORY for quali)
```

**Fix**: Ensure `build_rlt_session()` adds Q1 field for all qualification drivers:
```python
if session_type == "Qualification":
    driver['Q1'] = format_ms_short(time_ms)
```

### Pytest Fails: Q1 Format Invalid

```
❌ Driver 3 (Charles Leclerc) Q1 format invalid: '1:16:899' (expected 'm:ss.mmm')
```

**Fix**: Use correct format with **colon** (`:`) between minutes and seconds, **dot** (`.`) before milliseconds:
```python
format_ms_short(76899)  # → "1:16.899" ✅
```

### Coverage Too Low

```
FAIL Required test coverage of 92% not reached. Total coverage: 85.34%
```

**Fix**: Add integration tests that execute adapter code:
- Test `build_rlt_session()` with mock payloads
- Test mapping functions (`get_team_name()`, `get_driver_nation()`, etc.)
- Test enum mappers (`_map_session_type()`, `_map_weather()`, etc.)

---

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `tools/validate_rlt_quali.py` | Fast schema validator | 179 |
| `tests/test_quali_schema.py` | Golden fixture regression tests | 285 |
| `tests/fixtures/mexico_2025_quali.json` | Golden qualification fixture | 83 |
| `ft_mexico_export.py` | Field test with validation | 143 |
| `pytest.ini` | Pytest config (92% coverage) | 60 |

---

## References

- **Admin-Spec**: `rlt_import_session_results_json_format.txt`
- **Phase C++ H1**: Commit 57b00a2 (Unified Mapping Authority)
- **Adapter Fix**: Commit 60ce676 (Admin-Spec Compliance)
- **Full Report**: `docs/ADAPTER_FIX_REPORT.md`

---

**Last Updated**: 2025-11-02  
**Status**: ✅ Active - All gates passing
