import pandas as pd
import plotly.express as px

RISK_LEVEL_COLORS = {
    "Low": "#F4D03F",
    "Medium": "#E67E22",
    "High": "#E74C3C",
}


def risk_distribution_chart(records: list[dict]):
    df = pd.DataFrame(records)
    if df.empty:
        return None
    summary = df.groupby("risk_level", as_index=False).size().rename(columns={"size": "count"})
    order = [level for level in ("Low", "Medium", "High") if level in summary["risk_level"].values]
    color_map = {level: RISK_LEVEL_COLORS[level] for level in order}
    return px.bar(
        summary,
        x="risk_level",
        y="count",
        color="risk_level",
        color_discrete_map=color_map,
        category_orders={"risk_level": order},
        title="Dropout risk distribution",
    )
