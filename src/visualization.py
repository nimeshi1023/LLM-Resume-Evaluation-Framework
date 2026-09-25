import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_FILE = "results/evaluation_results.csv"
CHARTS_DIR = "charts"


def plot_category_accuracy(df):
    accuracy = (
        df.assign(correct=df["expected_decision"] == df["actual_decision"])
        .groupby("category")["correct"]
        .mean()
        .sort_values()
    )

    plt.figure(figsize=(8, 5))
    accuracy.plot(kind="barh", color="#4C72B0")
    plt.xlabel("Accuracy")
    plt.title("Decision Accuracy by Test Category")
    plt.xlim(0, 1)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "category_accuracy.png"), dpi=150)
    plt.close()


def plot_decision_distribution(df):
    expected_counts = df["expected_decision"].value_counts()
    actual_counts = df["actual_decision"].value_counts()

    labels = sorted(set(expected_counts.index) | set(actual_counts.index))

    expected_values = [expected_counts.get(label, 0) for label in labels]
    actual_values = [actual_counts.get(label, 0) for label in labels]

    x = range(len(labels))
    width = 0.35

    plt.figure(figsize=(8, 5))
    plt.bar([i - width / 2 for i in x], expected_values, width, label="Expected")
    plt.bar([i + width / 2 for i in x], actual_values, width, label="Actual")
    plt.xticks(list(x), labels, rotation=20)
    plt.ylabel("Count")
    plt.title("Expected vs Actual Decision Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "decision_distribution.png"), dpi=150)
    plt.close()


def plot_confusion_matrix(df):
    labels = sorted(
        set(df["expected_decision"]) | set(df["actual_decision"].dropna())
    )

    matrix = pd.DataFrame(0, index=labels, columns=labels)

    for _, row in df.iterrows():
        actual = row["actual_decision"]
        if pd.isna(actual):
            continue
        matrix.loc[row["expected_decision"], actual] += 1

    plt.figure(figsize=(6, 5))
    plt.imshow(matrix.values, cmap="Blues")
    plt.colorbar(label="Count")
    plt.xticks(range(len(labels)), labels, rotation=20)
    plt.yticks(range(len(labels)), labels)
    plt.xlabel("Actual Decision")
    plt.ylabel("Expected Decision")
    plt.title("Confusion Matrix (Decision)")

    for i in range(len(labels)):
        for j in range(len(labels)):
            plt.text(
                j, i, matrix.values[i, j],
                ha="center", va="center", color="black"
            )

    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "confusion_matrix.png"), dpi=150)
    plt.close()


def main():
    if not os.path.exists(RESULTS_FILE):
        raise FileNotFoundError(
            f"{RESULTS_FILE} not found. Run run_evaluation.py first."
        )

    os.makedirs(CHARTS_DIR, exist_ok=True)

    df = pd.read_csv(RESULTS_FILE)

    plot_category_accuracy(df)
    plot_decision_distribution(df)
    plot_confusion_matrix(df)

    print(f"Charts saved to: {CHARTS_DIR}/")
    print(" - category_accuracy.png")
    print(" - decision_distribution.png")
    print(" - confusion_matrix.png")


if __name__ == "__main__":
    main()