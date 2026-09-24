import pandas as pd
import json
import time

from llm_client import call_llm


INPUT_FILE = "data/test_cases.csv"
OUTPUT_FILE = "results/evaluation_results.csv"


df = pd.read_csv(INPUT_FILE)

results = []

for index, row in df.iterrows():

    print(f"Running {row['test_id']} ({index + 1}/{len(df)})")

    start_time = time.time()

    response = call_llm(
        row["job_description"],
        row["resume"]
    )

    latency = time.time() - start_time

    results.append({
        "test_id": row["test_id"],
        "category": row["category"],
        "expected_decision": row["expected_decision"],
        "actual_decision": response.get("decision"),
        "expected_matched_skills": row["expected_matched_skills"],
        "actual_matched_skills": ";".join(
            response.get("matched_skills", [])
        ),
        "expected_missing_skills": row["expected_missing_skills"],
        "actual_missing_skills": ";".join(
            response.get("missing_skills", [])
        ),
        "expected_experience_match":
            row["expected_experience_match"],

        "actual_experience_match":
            response.get("experience_match"),

        "expected_education_match":
            row["expected_education_match"],

        "actual_education_match":
            response.get("education_match"),

        "reason": response.get("reason"),

        "latency_seconds": round(latency, 2)
    })

    time.sleep(1)


results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nEvaluation completed.")
print(f"Saved to: {OUTPUT_FILE}")