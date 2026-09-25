import os
import re
import pandas as pd

TEST_CASES_FILE = "data/test_cases.csv"
RESULTS_FILE = "results/evaluation_results.csv"
OUTPUT_FILE = "results/hallucination_report.csv"


def normalize(text):
    return re.sub(r"[^a-z0-9 ]", " ", str(text).lower())


def skill_in_resume(skill, resume_text):
    """
    Loose 'grounding' check: a skill counts as grounded if its normalized
    text appears as a substring of the normalized resume, or if every
    meaningful word in the skill appears somewhere in the resume text.
    This tolerates small wording differences (e.g. 'REST API' vs
    'REST APIs') while still catching skills the model invented outright.
    """
    norm_skill = normalize(skill).strip()
    norm_resume = normalize(resume_text)

    if norm_skill == "":
        return True

    if norm_skill in norm_resume:
        return True

    words = [w for w in norm_skill.split() if len(w) > 2]
    if not words:
        return True

    return all(word in norm_resume for word in words)


def main():
    if not os.path.exists(RESULTS_FILE):
        raise FileNotFoundError(
            f"{RESULTS_FILE} not found. Run run_evaluation.py first."
        )

    os.makedirs("results", exist_ok=True)

    results_df = pd.read_csv(RESULTS_FILE)
    cases_df = pd.read_csv(TEST_CASES_FILE)[["test_id", "resume"]]

    merged = results_df.merge(cases_df, on="test_id", how="left")

    flagged_rows = []
    total_claimed_skills = 0
    total_hallucinated_skills = 0

    for _, row in merged.iterrows():

        actual_matched = row.get("actual_matched_skills")

        if pd.isna(actual_matched) or str(actual_matched).strip() == "":
            continue

        skills = [
            s.strip() for s in str(actual_matched).split(";") if s.strip() != ""
        ]

        hallucinated_skills = [
            s for s in skills if not skill_in_resume(s, row["resume"])
        ]

        total_claimed_skills += len(skills)
        total_hallucinated_skills += len(hallucinated_skills)

        if hallucinated_skills:
            flagged_rows.append({
                "test_id": row["test_id"],
                "category": row["category"],
                "hallucinated_skills": ";".join(hallucinated_skills),
                "resume_excerpt": str(row["resume"]).strip()[:200],
            })

    flagged_df = pd.DataFrame(flagged_rows)
    flagged_df.to_csv(OUTPUT_FILE, index=False)

    hallucination_rate = (
        total_hallucinated_skills / total_claimed_skills
        if total_claimed_skills > 0
        else 0.0
    )

    print(f"Total claimed skills checked: {total_claimed_skills}")
    print(f"Skills not found in resume text: {total_hallucinated_skills}")
    print(f"Hallucination rate: {hallucination_rate:.2%}")
    print(f"\nFlagged cases saved to: {OUTPUT_FILE}")

    if not flagged_df.empty:
        print("\nFlagged test cases:")
        print(flagged_df.to_string(index=False))
    else:
        print("\nNo hallucinated skills detected.")


if __name__ == "__main__":
    main()