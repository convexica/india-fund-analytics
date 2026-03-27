import json
import os
import sys

# Add root for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.data_fetcher import MFDataFetcher  # noqa: E402


def find_best_code(all_schemes, search_name):
    # Ensure it's Direct Growth
    options = []
    for code, full_name in all_schemes.items():
        if search_name.lower() in full_name.lower() and "direct" in full_name.lower() and "growth" in full_name.lower():
            # Exclude IDCW/Bonus
            if "idcw" not in full_name.lower() and "bonus" not in full_name.lower():
                options.append((code, full_name))
    
    if not options:
        return None, None
        
    # Pick the one with shortest name or most standard "Direct Plan-Growth"
    # Usually looking for "Direct Plan-Growth" or "Direct Growth"
    options.sort(key=lambda x: len(x[1]))
    return options[0]

def main():
    fetcher = MFDataFetcher()
    all_schemes = fetcher.get_all_schemes()
    
    user_names = [
        "Parag Parikh Flexi Cap",
        "HDFC Balanced Advantage",
        "HDFC Flexi Cap",
        "HDFC Mid Cap",
        "ICICI Prudential Multi-Asset",
        "SBI Equity Hybrid",
        "ICICI Prudential Bluechip",
        "ICICI Prudential Balanced Advantage",
        "Nippon India Small Cap",
        "Kotak Midcap",
        "ICICI Prudential Value Discovery",
        "Kotak Flexicap",
        "SBI Large Cap",
        "Nippon India Large Cap",
        "Nippon India Multi Cap",
        "ICICI Prudential Equity & Debt",
        "SBI Contra",
        "Nippon India Growth",
        "SBI Focused",
        "Mirae Asset Large & Midcap",
        "SBI Balanced Advantage",
        "Mirae Asset Large Cap",
        "HDFC Large Cap",
        "SBI Large & Midcap",
        "HDFC Small Cap",
        "ICICI Prudential India Opportunities",
        "SBI Small Cap",
        "Motilal Oswal Midcap",
        "Axis Large Cap",
        "Axis Midcap",
        "Kotak Large & Midcap",
        "Aditya Birla SL Large Cap",
        "HDFC Large and Mid Cap",
        "ICICI Prudential Large & Mid Cap",
        "Quant Small Cap",
        "HDFC Focused",
        "Axis Small Cap",
        "Aditya Birla SL Flexi Cap",
        "Canara Robeco Large and Mid Cap",
        "Kotak Multicap",
        "HDFC Hybrid Equity",
        "SBI Flexicap",
        "SBI Midcap",
        "SBI Multicap",
        "UTI Flexi Cap",
        "Bandhan Small Cap",
        "ICICI Prudential Flexicap",
        "Invesco India Contra",
        "DSP Midcap",
        "Franklin India Flexi Cap",
    ]
    
    results = {}
    for name in user_names:
        code, full_name = find_best_code(all_schemes, name)
        if code:
            results[code] = full_name
        else:
            # Try some variations
            if "AXIS LARGE CAP" in name.upper():
                code, full_name = find_best_code(all_schemes, "Axis Bluechip")
            elif "ICICI PRUDENTIAL BLUECHIP" in name.upper():
                 code, full_name = find_best_code(all_schemes, "ICICI Prudential Bluechip")
                 
            if code:
                results[code] = full_name
            else:
                print(f"MISSING: {name}")

    print("\nFINAL MAPPING:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
