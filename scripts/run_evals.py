import json
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.schema import EnrichRequest
from src.llm.service import call_llm_enrichment

def run_evaluation():
    print("🚀 Starting Prompt Evaluation Suite...")
    
    eval_path = "evals/cases.json"
    if not os.path.exists(eval_path):
        print("❌ Error: evals/cases.json not found.")
        return

    with open(eval_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0
    failed = 0

    for idx, case in enumerate(cases, 1):
        print(f"\n--- Running Test Case {idx}: {case['description']} ---")
        try:
            payload = EnrichRequest(**case["input"])
            response = call_llm_enrichment(payload)
            
            exp = case["expected"]
            errors = []

            # Check Category
            if response.category != exp.get("category"):
                errors.append(f"Expected category '{exp.get('category')}', got '{response.category}'")

            # Check Confidence bounds
            if "min_confidence" in exp and response.confidence < exp["min_confidence"]:
                errors.append(f"Confidence {response.confidence} is below minimum {exp['min_confidence']}")
            if "max_confidence" in exp and response.confidence > exp["max_confidence"]:
                errors.append(f"Confidence {response.confidence} is above maximum {exp['max_confidence']}")

            # Check Required Flags
            if "required_flag" in exp and exp["required_flag"] not in response.quality_flags:
                errors.append(f"Required quality flag '{exp['required_flag']}' missing from {response.quality_flags}")

            if errors:
                print(f"❌ Test Case {idx} FAILED:")
                for err in errors:
                    print(f"   - {err}")
                failed += 1
            else:
                print(f"✅ Test Case {idx} PASSED!")
                passed += 1

        except Exception as e:
            print(f"❌ Test Case {idx} CRASHED with exception: {str(e)}")
            failed += 1

    print(f"\n==============================")
    print(f"📊 Evaluation Complete: {passed} Passed, {failed} Failed")
    print(f"==============================")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_evaluation()