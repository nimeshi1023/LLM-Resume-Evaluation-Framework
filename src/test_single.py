import pandas as pd
from llm_client import call_llm

df = pd.read_csv("data/test_cases.csv")

test = df.iloc[0]

result = call_llm(
    test["job_description"],
    test["resume"]
)

print("TEST ID:", test["test_id"])
print("EXPECTED:", test["expected_decision"])
print("ACTUAL:", result)