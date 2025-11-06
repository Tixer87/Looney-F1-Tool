# Looney F1 Tool — v1.7.2_beta

The F1 data exporter that turns **Jolpica / FastF1** sessions into **Racing League Tools-ready JSON**.  
Now with **Qualifying split** (Q → Q1/Q2/Q3) and **Full Event Export**.

![Looney F1 v1.7.2_beta](https://img.shields.io/badge/Looney%20F1-v1.7.2_beta-magenta?style=for-the-badge&logo=formula1)

## Highlights
- **Qualifying split:** one Q session → three JSON files **Q1/Q2/Q3** (RLT import)
- **Full Event Export:** FP1, FP2, FP3, Q1–Q3, Sprint (if present), Race
- **Validators & Tests:** official-results check, quali-sanity-check, pytest

## Quick start
1. Download the ZIP from the latest release  
2. Extract and run LooneyF1Tool.exe  
3. Choose **Season** and **Round**, click **All Sessions**  
4. Quali Q1/Q2/Q3 + Race land in your export folder

## Tools
- 	ools/validate_official_results.py
- 	ools/check_quali_exports.py
- 	ools/export_batch.py

## Notes
- All times are **integer ms**
- Team mapping separates **Red Bull** and **Racing Bulls**
- Works with Jolpica/FastF1 data (2025 season)
