import os
import pandas as pd
import time

from llm_client import call_llm


# ============================================================
# File paths
# ============================================================

INPUT_FILE = "data/test_cases.csv"
OUTPUT_FILE = "results/evaluation_results.csv"


# ============================================================
# Make sure results folder exists
# ============================================================

os.makedirs("results", exist_ok=True)


# ============================================================
# Load test cases
# ============================================================

df = pd.read_csv(INPUT_FILE)

print(f"Total test cases: {len(df)}")


# ============================================================
# Load previous results
# ============================================================

if os.path.exists(OUTPUT_FILE):

    print(f"\nExisting results found: {OUTPUT_FILE}")

    results_df = pd.read_csv(OUTPUT_FILE)

    # Make sure test_id is string
    results_df["test_id"] = (
        results_df["test_id"]
        .astype(str)
    )

    completed_ids = set(
        results_df["test_id"]
    )

    print(
        f"Already completed: "
        f"{len(completed_ids)} test case(s)"
    )

else:

    print("\nNo previous results found.")
    print("Starting evaluation from the beginning.")

    results_df = pd.DataFrame(
        columns=[
            "test_id",
            "category",
            "difficulty",

            "expected_decision",
            "actual_decision",

            "expected_matched_skills",
            "actual_matched_skills",

            "expected_missing_skills",
            "actual_missing_skills",

            "expected_experience_match",
            "actual_experience_match",

            "expected_education_match",
            "actual_education_match",

            "reason",
            "latency_seconds"
        ]
    )

    completed_ids = set()


# ============================================================
# Run evaluation
# ============================================================

for index, row in df.iterrows():

    test_id = str(row["test_id"])


    # --------------------------------------------------------
    # Skip already completed tests
    # --------------------------------------------------------

    if test_id in completed_ids:

        print(
            f"Skipping {test_id} "
            f"({index + 1}/{len(df)}) - already completed"
        )

        continue


    print("\n" + "=" * 60)

    print(
        f"Running {test_id} "
        f"({index + 1}/{len(df)})"
    )

    print("=" * 60)


    # --------------------------------------------------------
    # Start latency timer
    # --------------------------------------------------------

    start_time = time.time()


    try:

        # ----------------------------------------------------
        # Call Gemini
        # ----------------------------------------------------

        response = call_llm(
            row["job_description"],
            row["resume"]
        )


        # ----------------------------------------------------
        # Calculate latency
        # ----------------------------------------------------

        latency = time.time() - start_time


        # ----------------------------------------------------
        # Create result row
        # ----------------------------------------------------

        new_result = {
            "test_id": test_id,

            "category": row["category"],

            "difficulty": row["difficulty"],


            # Decision
            "expected_decision": row["expected_decision"],

            "actual_decision": response.get(
                "decision"
            ),


            # Matched skills
            "expected_matched_skills": (
                row["expected_matched_skills"]
            ),

            "actual_matched_skills": ";".join(
                response.get(
                    "matched_skills",
                    []
                ) or []
            ),


            # Missing skills
            "expected_missing_skills": (
                row["expected_missing_skills"]
            ),

            "actual_missing_skills": ";".join(
                response.get(
                    "missing_skills",
                    []
                ) or []
            ),


            # Experience
            "expected_experience_match": (
                row["expected_experience_match"]
            ),

            "actual_experience_match": (
                response.get(
                    "experience_match"
                )
            ),


            # Education
            "expected_education_match": (
                row["expected_education_match"]
            ),

            "actual_education_match": (
                response.get(
                    "education_match"
                )
            ),


            # Reason
            "reason": response.get(
                "reason"
            ),


            # Latency
            "latency_seconds": round(
                latency,
                2
            )
        }


        # ----------------------------------------------------
        # Add result to DataFrame
        # ----------------------------------------------------

        results_df = pd.concat(
            [
                results_df,
                pd.DataFrame([new_result])
            ],
            ignore_index=True
        )


        # ----------------------------------------------------
        # Save IMMEDIATELY
        # ----------------------------------------------------

        results_df.to_csv(
            OUTPUT_FILE,
            index=False
        )


        # ----------------------------------------------------
        # Show result
        # ----------------------------------------------------

        expected = row["expected_decision"]

        actual = response.get(
            "decision"
        )


        print(
            f"\nExpected decision: {expected}"
        )

        print(
            f"Actual decision:   {actual}"
        )

        print(
            f"Latency:           {round(latency, 2)} seconds"
        )


        if expected == actual:

            print("RESULT: PASS")

        else:

            print("RESULT: FAIL")


        print(
            f"Saved to: {OUTPUT_FILE}"
        )


        # ----------------------------------------------------
        # Small delay between API requests
        # ----------------------------------------------------

        time.sleep(1)


    except RuntimeError as e:

        error_message = str(e)


        # ====================================================
        # Gemini daily limit
        # ====================================================

        if error_message == "GEMINI_DAILY_LIMIT_REACHED":

            print("\n" + "=" * 60)

            print(
                "GEMINI DAILY LIMIT REACHED"
            )

            print("=" * 60)

            print(
                "Evaluation stopped safely."
            )

            print(
                "All completed results have already been saved."
            )

            print(
                f"Results file: {OUTPUT_FILE}"
            )

            print(
                "\nRun this script again later."
            )

            print(
                "Completed test cases will be skipped "
                "automatically."
            )

            break


        # ====================================================
        # Temporary Gemini error
        # ====================================================

        elif error_message == "GEMINI_TEMPORARY_UNAVAILABLE":

            print(
                f"\nTemporary Gemini error on {test_id}."
            )

            print(
                "Skipping this test and continuing..."
            )

            continue


        # ====================================================
        # Other errors
        # ====================================================

        else:

            print(
                f"\nERROR while running {test_id}:"
            )

            print(error_message)

            print(
                "Skipping this test and continuing..."
            )

            continue


    except KeyboardInterrupt:

        print("\n" + "=" * 60)

        print(
            "Evaluation manually stopped by user."
        )

        print("=" * 60)

        print(
            "Completed results have already been saved."
        )

        print(
            f"Results file: {OUTPUT_FILE}"
        )

        print(
            "\nRun the script again later to resume."
        )

        break


# ============================================================
# Final Summary
# ============================================================

print("\n" + "=" * 60)
print("EVALUATION SUMMARY")
print("=" * 60)


# ------------------------------------------------------------
# Reload final results from CSV
# ------------------------------------------------------------

if os.path.exists(OUTPUT_FILE):

    final_df = pd.read_csv(
        OUTPUT_FILE
    )

else:

    final_df = results_df


# ------------------------------------------------------------
# No results check
# ------------------------------------------------------------

if final_df.empty:

    print(
        "\nNo test cases were completed."
    )

else:

    # ========================================================
    # Decision correctness
    # ========================================================

    final_df["decision_correct"] = (
        final_df["expected_decision"]
        == final_df["actual_decision"]
    )


    # ========================================================
    # Overall accuracy
    # ========================================================

    overall_accuracy = (
        final_df["decision_correct"]
        .mean()
    )


    print(
        f"\nCompleted test cases: "
        f"{len(final_df)}/{len(df)}"
    )

    print(
        f"Overall decision accuracy: "
        f"{overall_accuracy:.2%}"
    )


    # ========================================================
    # Accuracy by category
    # ========================================================

    print("\nAccuracy by category:")

    category_accuracy = (
        final_df
        .groupby("category")["decision_correct"]
        .mean()
    )


    for category, accuracy in category_accuracy.items():

        print(
            f"  {category}: "
            f"{accuracy:.2%}"
        )


    # ========================================================
    # Accuracy by difficulty
    # ========================================================

    if "difficulty" in final_df.columns:

        print("\nAccuracy by difficulty:")

        difficulty_accuracy = (
            final_df
            .groupby("difficulty")["decision_correct"]
            .mean()
        )


        for difficulty, accuracy in (
            difficulty_accuracy.items()
        ):

            print(
                f"  {difficulty}: "
                f"{accuracy:.2%}"
            )


    # ========================================================
    # Average latency
    # ========================================================

    if "latency_seconds" in final_df.columns:

        average_latency = (
            final_df["latency_seconds"]
            .mean()
        )


        print(
            f"\nAverage latency: "
            f"{average_latency:.2f} seconds"
        )


    # ========================================================
    # Failed cases
    # ========================================================

    failures = final_df[
        ~final_df["decision_correct"]
    ]


    if not failures.empty:

        print(
            f"\nFailed cases: "
            f"{len(failures)}"
        )

        print()

        print(
            failures[
                [
                    "test_id",
                    "category",
                    "expected_decision",
                    "actual_decision"
                ]
            ].to_string(
                index=False
            )
        )

    else:

        print(
            "\nAll completed test cases "
            "matched the expected decision."
        )


# ============================================================
# Final file location
# ============================================================

print("\n" + "=" * 60)

print(
    f"Results saved to:"
)

print(
    OUTPUT_FILE
)

print("=" * 60)