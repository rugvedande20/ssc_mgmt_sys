import pandas as pd
import plotly.express as px


def risk_distribution_chart(records: list[dict]):
    df = pd.DataFrame(records)
    if df.empty:
        return None
    summary = df.groupby("risk_level", as_index=False).size().rename(columns={"size": "count"})
    return px.bar(summary, x="risk_level", y="count", color="risk_level", title="Dropout Risk Distribution")
