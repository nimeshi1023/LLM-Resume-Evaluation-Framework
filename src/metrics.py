import os
import pandas as pd

RESULTS_FILE = "results/evaluation_results.csv"
OUTPUT_FILE = "results/summary_metrics.csv"


def parse_list(value):
    """Split a semicolon-separated string into a clean, lowercase set."""
    if pd.isna(value) or str(value).strip() == "":
        return set()
    return set(
        item.strip().lower()
        for item in str(value).split(";")
        if item.strip() != ""
    )


def decision_confusion_matrix(df):
    labels = sorted(
        set(df["expected_decision"]) | set(df["actual_decision"].dropna())
    )

    matrix = pd.DataFrame(0, index=labels, columns=labels)

    for _, row in df.iterrows():
        actual = row["actual_decision"]
        if pd.isna(actual):
            continue
        matrix.loc[row["expected_decision"], actual] += 1

    return matrix


def macro_precision_recall_f1(df):
    labels = sorted(set(df["expected_decision"]))

    precisions, recalls, f1s = [], [], []

    for label in labels:
        tp = len(df[(df["expected_decision"] == label) & (df["actual_decision"] == label)])
        fp = len(df[(df["expected_decision"] != label) & (df["actual_decision"] == label)])
        fn = len(df[(df["expected_decision"] == label) & (df["actual_decision"] != label)])

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    return (
        sum(precisions) / len(precisions),
        sum(recalls) / len(recalls),
        sum(f1s) / len(f1s),
    )


def skill_level_scores(df, expected_col, actual_col):
    tp_total = fp_total = fn_total = 0

    for _, row in df.iterrows():
        expected = parse_list(row[expected_col])
        actual = parse_list(row[actual_col])

        tp_total += len(expected & actual)
        fp_total += len(actual - expected)
        fn_total += len(expected - actual)

    precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
    recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return precision, recall, f1


def field_accuracy(df, expected_col, actual_col):
    matches = (
        df[expected_col].astype(str).str.lower()
        == df[actual_col].astype(str).str.lower()
    )
    return matches.mean()


def main():
    if not os.path.exists(RESULTS_FILE):
        raise FileNotFoundError(
            f"{RESULTS_FILE} not found. Run run_evaluation.py first."
        )

    os.makedirs("results", exist_ok=True)

    df = pd.read_csv(RESULTS_FILE)

    # =========================================================
    # Decision metrics
    # =========================================================

    overall_accuracy = field_accuracy(df, "expected_decision", "actual_decision")
    precision, recall, f1 = macro_precision_recall_f1(df)

    confusion = decision_confusion_matrix(df)
    confusion.to_csv("results/confusion_matrix.csv")

    # =========================================================
    # Skill-level metrics (treated as multi-label per case)
    # =========================================================

    matched_precision, matched_recall, matched_f1 = skill_level_scores(
        df, "expected_matched_skills", "actual_matched_skills"
    )

    missing_precision, missing_recall, missing_f1 = skill_level_scores(
        df, "expected_missing_skills", "actual_missing_skills"
    )

    # =========================================================
    # Field-level accuracy
    # =========================================================

    experience_accuracy = field_accuracy(
        df, "expected_experience_match", "actual_experience_match"
    )
    education_accuracy = field_accuracy(
        df, "expected_education_match", "actual_education_match"
    )

    # =========================================================
    # Per-category accuracy
    # =========================================================

    category_accuracy = (
        df.assign(correct=df["expected_decision"] == df["actual_decision"])
        .groupby("category")["correct"]
        .mean()
    )

    # =========================================================
    # Assemble and save summary
    # =========================================================

    summary_rows = [
        {"metric": "overall_decision_accuracy", "value": round(overall_accuracy, 4)},
        {"metric": "decision_precision_macro", "value": round(precision, 4)},
        {"metric": "decision_recall_macro", "value": round(recall, 4)},
        {"metric": "decision_f1_macro", "value": round(f1, 4)},
        {"metric": "matched_skills_precision", "value": round(matched_precision, 4)},
        {"metric": "matched_skills_recall", "value": round(matched_recall, 4)},
        {"metric": "matched_skills_f1", "value": round(matched_f1, 4)},
        {"metric": "missing_skills_precision", "value": round(missing_precision, 4)},
        {"metric": "missing_skills_recall", "value": round(missing_recall, 4)},
        {"metric": "missing_skills_f1", "value": round(missing_f1, 4)},
        {"metric": "experience_match_accuracy", "value": round(experience_accuracy, 4)},
        {"metric": "education_match_accuracy", "value": round(education_accuracy, 4)},
        {"metric": "average_latency_seconds", "value": round(df["latency_seconds"].mean(), 4)},
    ]

    for category, acc in category_accuracy.items():
        summary_rows.append(
            {"metric": f"category_accuracy_{category}", "value": round(acc, 4)}
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUTPUT_FILE, index=False)

    print("Metrics saved to:", OUTPUT_FILE)
    print("Confusion matrix saved to: results/confusion_matrix.csv\n")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()