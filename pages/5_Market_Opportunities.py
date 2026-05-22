from common.scoring import rank_market

ranked_df = rank_market(df)

st.dataframe(
    ranked_df[[
        "Symbol",
        "Stock Score",
        "ROE",
        "PE Ratio",
        "RSI"
    ]].head(25)
)
