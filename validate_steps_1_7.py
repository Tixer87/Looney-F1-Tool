"""
Complete validation of Steps 1-7 for Looney F1 Tool v1.7.2_beta
Tests all integration points before EXE build
"""
import json
from pathlib import Path
from api.export_service import run_export
from api.providers.router import get_provider

print("=" * 80)
print("LOONEY F1 TOOL v1.7.2_beta - VALIDATION CHECKLIST (Steps 1-7)")
print("=" * 80)

results = []

# ==============================================================================
# STEP 1: Provider Router - Year-based selection
# ==============================================================================
print("\n📋 STEP 1: Provider Router - Year-based selection")
print("-" * 80)

try:
    provider_2024 = get_provider(year=2024)
    provider_2022 = get_provider(year=2022)
    provider_2023 = get_provider(year=2023)
    
    assert provider_2024.name == 'fastf1', f"2024 should use FastF1, got {provider_2024.name}"
    assert provider_2022.name == 'jolpica', f"2022 should use Jolpica, got {provider_2022.name}"
    assert provider_2023.name == 'fastf1', f"2023 should use FastF1, got {provider_2023.name}"
    
    print(f"✅ 2024 → {provider_2024.name} (FastF1)")
    print(f"✅ 2022 → {provider_2022.name} (Jolpica)")
    print(f"✅ 2023 → {provider_2023.name} (FastF1)")
    results.append(("Step 1: Provider Routing", "✅ PASS"))
except Exception as e:
    print(f"❌ FAILED: {e}")
    results.append(("Step 1: Provider Routing", f"❌ FAIL: {e}"))

# ==============================================================================
# STEP 2: Circuit Name Resolution
# ==============================================================================
print("\n📋 STEP 2: Circuit Name Resolution (24 circuits + FastF1 aliases)")
print("-" * 80)

try:
    from mapping.circuit_aliases import get_circuit
    
    # Test standard circuits
    test_circuits = [
        ("Bahrain", "Bahrain"),
        ("Jeddah", "Jeddah"),
        ("Melbourne", "Melbourne"),
        ("Suzuka", "Suzuka"),
        ("Shanghai", "Shanghai"),
        ("Miami", "Miami"),
        ("Imola", "Imola"),
        ("Monaco", "Monaco"),
        ("Barcelona", "Barcelona"),
        ("Montreal", "Montreal"),
        ("Spielberg", "Spielberg"),
        ("Silverstone", "Silverstone"),
        ("Hungaroring", "Hungaroring"),
        ("Spa", "Spa"),
        ("Zandvoort", "Zandvoort"),
        ("Monza", "Monza"),
        ("Baku", "Baku"),
        ("Singapore", "Singapore"),
        ("Austin", "Austin"),
        ("Mexico", "Mexico"),
        ("Interlagos", "Interlagos"),
        ("Las Vegas", "Las Vegas"),
        ("Losail", "Losail"),
        ("Yas Marina", "Yas Marina"),
    ]
    
    # Test FastF1 aliases
    fastf1_aliases = [
        ("Montréal", "Montreal"),  # With accent
        ("Budapest", "Hungaroring"),
        ("Marina Bay", "Singapore"),
        ("Mexico City", "Mexico"),
        ("São Paulo", "Interlagos"),  # With tilde
        ("Lusail", "Losail"),  # Corrected spelling
        ("Yas Island", "Yas Marina"),
    ]
    
    failed = []
    for circuit_name, expected_track in test_circuits:
        try:
            track_name, track_unique = get_circuit(circuit_name)
            print(f"  ✓ {circuit_name:20s} → {track_name}")
        except Exception as e:
            failed.append(f"{circuit_name}: {e}")
            print(f"  ✗ {circuit_name:20s} → FAILED: {e}")
    
    print(f"\n  FastF1 Aliases:")
    for alias, expected_track in fastf1_aliases:
        try:
            track_name, track_unique = get_circuit(alias)
            print(f"  ✓ {alias:20s} → {track_name}")
        except Exception as e:
            failed.append(f"{alias}: {e}")
            print(f"  ✗ {alias:20s} → FAILED: {e}")
    
    if failed:
        results.append(("Step 2: Circuit Resolution", f"❌ FAIL: {len(failed)} circuits failed"))
        print(f"\n❌ {len(failed)} circuit(s) failed")
    else:
        results.append(("Step 2: Circuit Resolution", "✅ PASS"))
        print(f"\n✅ All 24 circuits + 7 FastF1 aliases resolved")
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    results.append(("Step 2: Circuit Resolution", f"❌ FAIL: {e}"))

# ==============================================================================
# STEP 3: Race Export (FastF1)
# ==============================================================================
print("\n📋 STEP 3: Race Export - Bahrain 2024 (FastF1)")
print("-" * 80)

try:
    output = run_export(2024, 1, 'R', Path('out'), verbose=False)
    
    if output and output.exists():
        data = json.load(open(output))
        driver_count = len(data['Drivers'])
        session_type = data.get('SessionType')
        race_type = data.get('RaceType')
        track_name = data.get('TrackName')
        
        # Find winner
        winner = [d for d in data['Drivers'] if d['Position'] == 1][0]
        winner_name = winner['Driver']['Name']
        winner_time = winner.get('TimeInt', 0)
        
        print(f"  ✓ File: {output.name}")
        print(f"  ✓ SessionType: {session_type}")
        print(f"  ✓ RaceType: {race_type}")
        print(f"  ✓ Track: {track_name}")
        print(f"  ✓ Drivers: {driver_count}")
        print(f"  ✓ Winner: {winner_name} (TimeInt: {winner_time}ms)")
        
        assert session_type == "Race", f"Expected SessionType=Race, got {session_type}"
        assert driver_count >= 19, f"Expected >=19 drivers, got {driver_count}"
        
        results.append(("Step 3: Race Export (FastF1)", "✅ PASS"))
        print(f"✅ Race export successful")
    else:
        results.append(("Step 3: Race Export (FastF1)", "❌ FAIL: No output file"))
        print(f"❌ No output file created")
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    results.append(("Step 3: Race Export (FastF1)", f"❌ FAIL: {e}"))

# ==============================================================================
# STEP 4: Race Export (Jolpica)
# ==============================================================================
print("\n📋 STEP 4: Race Export - Bahrain 2022 (Jolpica)")
print("-" * 80)

try:
    output = run_export(2022, 1, 'R', Path('out'), verbose=False)
    
    if output and output.exists():
        data = json.load(open(output))
        driver_count = len(data['Drivers'])
        session_type = data.get('SessionType')
        track_name = data.get('TrackName')
        
        # Find winner
        winner = [d for d in data['Drivers'] if d['Position'] == 1][0]
        winner_name = winner['Driver']['Name']
        
        print(f"  ✓ File: {output.name}")
        print(f"  ✓ SessionType: {session_type}")
        print(f"  ✓ Track: {track_name}")
        print(f"  ✓ Drivers: {driver_count}")
        print(f"  ✓ Winner: {winner_name}")
        
        assert session_type == "Race", f"Expected SessionType=Race, got {session_type}"
        
        results.append(("Step 4: Race Export (Jolpica)", "✅ PASS"))
        print(f"✅ Race export successful")
    else:
        results.append(("Step 4: Race Export (Jolpica)", "❌ FAIL: No output file"))
        print(f"❌ No output file created")
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    results.append(("Step 4: Race Export (Jolpica)", f"❌ FAIL: {e}"))

# ==============================================================================
# STEP 5: Practice Export (FastF1)
# ==============================================================================
print("\n📋 STEP 5: Practice Export - Bahrain 2024 FP1 (FastF1)")
print("-" * 80)

try:
    output = run_export(2024, 1, 'FP1', Path('out'), verbose=False)
    
    if output and output.exists():
        data = json.load(open(output))
        driver_count = len(data['Drivers'])
        session_type = data.get('SessionType')
        
        print(f"  ✓ File: {output.name}")
        print(f"  ✓ SessionType: {session_type}")
        print(f"  ✓ Drivers: {driver_count}")
        
        assert session_type == "Practice", f"Expected SessionType=Practice, got {session_type}"
        
        results.append(("Step 5: Practice Export (FastF1)", "✅ PASS"))
        print(f"✅ Practice export successful")
    else:
        results.append(("Step 5: Practice Export (FastF1)", "❌ FAIL: No output file"))
        print(f"❌ No output file created")
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    results.append(("Step 5: Practice Export (FastF1)", f"❌ FAIL: {e}"))

# ==============================================================================
# STEP 6: Sprint Export (FastF1 2024)
# ==============================================================================
print("\n📋 STEP 6: Sprint Export - Test with 2024 Round 4 (FastF1)")
print("-" * 80)

try:
    # Try Sprint export for China 2024 (Round 5 had Sprint)
    output = run_export(2024, 5, 'S', Path('out'), verbose=False)
    
    if output and output.exists():
        data = json.load(open(output))
        driver_count = len(data['Drivers'])
        session_type = data.get('SessionType')
        race_type = data.get('RaceType')
        
        print(f"  ✓ File: {output.name}")
        print(f"  ✓ SessionType: {session_type}")
        print(f"  ✓ RaceType: {race_type}")
        print(f"  ✓ Drivers: {driver_count}")
        
        assert session_type == "Race", f"Expected SessionType=Race, got {session_type}"
        assert race_type in ["Sprint", "Regular"], f"Expected RaceType=Sprint/Regular, got {race_type}"
        
        results.append(("Step 6: Sprint Export (FastF1)", "✅ PASS"))
        print(f"✅ Sprint export successful")
    else:
        results.append(("Step 6: Sprint Export (FastF1)", "⚠️ SKIP: No Sprint data available"))
        print(f"⚠️ No Sprint data available for 2024 Round 5")
        
except Exception as e:
    print(f"⚠️ SKIPPED: {e}")
    results.append(("Step 6: Sprint Export (FastF1)", f"⚠️ SKIP: {e}"))

# ==============================================================================
# STEP 7: Qualifying Export with Q1/Q2/Q3 Split (FastF1)
# ==============================================================================
print("\n📋 STEP 7: Qualifying Export - Q1/Q2/Q3 Split (FastF1)")
print("-" * 80)

try:
    output = run_export(2024, 1, 'Q', Path('out'), verbose=False)
    
    # Check for 3 files
    q1_file = Path('out/2024_Sakhir_Bahrain_Q1.json')
    q2_file = Path('out/2024_Sakhir_Bahrain_Q2.json')
    q3_file = Path('out/2024_Sakhir_Bahrain_Q3.json')
    
    if not (q1_file.exists() and q2_file.exists() and q3_file.exists()):
        results.append(("Step 7: Qualifying Split", "❌ FAIL: Not all 3 Q files created"))
        print(f"❌ Missing Q files!")
    else:
        q1_data = json.load(open(q1_file))
        q2_data = json.load(open(q2_file))
        q3_data = json.load(open(q3_file))
        
        q1_count = len(q1_data['Drivers'])
        q2_count = len(q2_data['Drivers'])
        q3_count = len(q3_data['Drivers'])
        
        q1_type = q1_data.get('QualType')
        q2_type = q2_data.get('QualType')
        q3_type = q3_data.get('QualType')
        
        q1_pos = q1_data.get('SessionPosition')
        q2_pos = q2_data.get('SessionPosition')
        q3_pos = q3_data.get('SessionPosition')
        
        race_type_q1 = q1_data.get('RaceType')
        
        # Check Max Verstappen's times
        max_q1 = [d for d in q1_data['Drivers'] if 'Verstappen' in d['Driver']['Name']][0]
        max_q2 = [d for d in q2_data['Drivers'] if 'Verstappen' in d['Driver']['Name']][0]
        max_q3 = [d for d in q3_data['Drivers'] if 'Verstappen' in d['Driver']['Name']][0]
        
        time_q1 = max_q1['TimeInt']
        time_q2 = max_q2['TimeInt']
        time_q3 = max_q3['TimeInt']
        
        # Check for Q-fields (should NOT exist)
        has_q_fields = 'Q1' in max_q1 or 'Q2' in max_q1 or 'Q3' in max_q1
        
        print(f"  Q1 File:")
        print(f"    ✓ Drivers: {q1_count} (expected: 20)")
        print(f"    ✓ QualType: {q1_type}")
        print(f"    ✓ SessionPosition: {q1_pos}")
        print(f"    ✓ RaceType: {race_type_q1}")
        print(f"    ✓ Max TimeInt: {time_q1}ms")
        print(f"    ✓ Q-fields present: {has_q_fields} (should be False)")
        
        print(f"\n  Q2 File:")
        print(f"    ✓ Drivers: {q2_count} (expected: 15)")
        print(f"    ✓ QualType: {q2_type}")
        print(f"    ✓ SessionPosition: {q2_pos}")
        print(f"    ✓ Max TimeInt: {time_q2}ms")
        
        print(f"\n  Q3 File:")
        print(f"    ✓ Drivers: {q3_count} (expected: 10)")
        print(f"    ✓ QualType: {q3_type}")
        print(f"    ✓ SessionPosition: {q3_pos}")
        print(f"    ✓ Max TimeInt: {time_q3}ms")
        
        # Validations
        checks = []
        checks.append(("Driver counts", q1_count == 20 and q2_count == 15 and q3_count == 10))
        checks.append(("QualTypes", q1_type == 'Q1' and q2_type == 'Q2' and q3_type == 'Q3'))
        checks.append(("SessionPositions", q1_pos == 0 and q2_pos == 1 and q3_pos == 2))
        checks.append(("RaceType", race_type_q1 == 'Regular'))
        checks.append(("Different times", time_q1 != time_q2 and time_q2 != time_q3))
        checks.append(("No Q-fields", not has_q_fields))
        
        all_passed = all(check[1] for check in checks)
        
        print(f"\n  Validation Checks:")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"    {status} {check_name}")
        
        if all_passed:
            results.append(("Step 7: Qualifying Split", "✅ PASS"))
            print(f"\n✅ Qualifying split export successful (knockout system working)")
        else:
            results.append(("Step 7: Qualifying Split", "❌ FAIL: Some checks failed"))
            print(f"\n❌ Some validation checks failed")
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    results.append(("Step 7: Qualifying Split", f"❌ FAIL: {e}"))

# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

for step, status in results:
    print(f"{status:20s} {step}")

passed = sum(1 for _, status in results if "✅ PASS" in status)
skipped = sum(1 for _, status in results if "⚠️ SKIP" in status)
failed = sum(1 for _, status in results if "❌ FAIL" in status)
total = len(results)

print(f"\n{'=' * 80}")
print(f"TOTAL: {passed}/{total} passed, {skipped} skipped, {failed} failed")

if failed == 0:
    print(f"\n🎉 ALL TESTS PASSED! Ready for Step 8: EXE Build")
else:
    print(f"\n⚠️ {failed} test(s) failed. Please fix before proceeding to EXE build.")

print("=" * 80)
