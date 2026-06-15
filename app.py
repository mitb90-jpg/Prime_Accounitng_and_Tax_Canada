import streamlit as st
import pandas as pd
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Transaction Categorizer",
    page_icon="📊",
    layout="wide"
)

# ---------------- CSS (BUTTON STYLING) ----------------
st.markdown("""
<style>
div.stDownloadButton > button {
    width: 100%;
    background-color: #1f4e79;
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 14px;
    border-radius: 12px;
    border: none;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
    transition: 0.3s;
}

div.stDownloadButton > button:hover {
    background-color: #163a5c;
    transform: scale(1.02);
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col1, col2 = st.columns([1, 6])

with col1:
    st.image("Logo.jpeg", width=100)

with col2:
    st.markdown(
        "<h1 style='color:#1f4e79;'>Prime Accounting and Tax</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='font-size:22px; color:gray;'>World Eyewear</p>",
        unsafe_allow_html=True
    )

# ---------------- SIDEBAR ----------------
company = st.sidebar.selectbox(
    "Select Account",
    ["Scotia Bank", "Triangle Master Card", "Visa - 6023", "Visa - 7866"]
)

uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

# ================= MAIN =================
if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    # ---------------- CLEAN ----------------
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all")

    df["Category"] = ""

    # ---------------- RULES ----------------
    df.loc[
        df["Credit"].notna() &
        df["Description"].astype(str).str.contains("MISC PAYMENT|TRANSFER FROM|DEPOSIT", case=False),
        "Category"
    ] = "Revenue"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.strip().str.lower().eq("misc payment"),
        "Category"
    ] = "Misc Expenses"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("INSURANCE", case=False),
        "Category"
    ] = "Insurance"

    # ---------------- TABLE ----------------
    st.subheader("📊 Categorized Transactions")
    st.dataframe(df, use_container_width=True)

    # ================= PROFIT & LOSS =================
    st.subheader("📊 Profit & Loss Statement")

    total_revenue = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()

    expense_df = df[df["Category"] != "Revenue"]
    expense_summary = expense_df.groupby("Category")["Debit"].sum().reset_index()

    total_expenses = expense_summary["Debit"].sum()
    net_profit = total_revenue - total_expenses

    pl_df = pd.DataFrame([
        ["Revenue", total_revenue],
        ["Less: Expenses", ""],
        *expense_summary.values.tolist(),
        ["Total Expenses", total_expenses],
        ["Net Profit", net_profit]
    ], columns=["Description", "Amount"])

    st.dataframe(pl_df, use_container_width=True)

    # ---------------- EXPORT P&L FILE ----------------
    pl_output = io.BytesIO()
    with pd.ExcelWriter(pl_output, engine="openpyxl") as writer:
        pl_df.to_excel(writer, index=False, sheet_name="Profit & Loss")

    pl_output.seek(0)

    st.download_button(
        "📊 Export Profit & Loss Statement",
        data=pl_output,
        file_name="Profit_and_Loss.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------- CATEGORY SUMMARY ----------------
    summary = df.groupby("Category")[["Credit", "Debit"]].sum().fillna(0)
    summary["Net"] = summary["Credit"] - summary["Debit"]

    st.subheader("📋 Category Summary")
    st.dataframe(summary.reset_index()[["Category", "Net"]])

    # ---------------- EXPORT TRANSACTIONS ----------------
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")

    output.seek(0)

    st.download_button(
        "⬇️ Export Categorized Data",
        data=output,
        file_name="Categorized_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload an Excel file to begin.")
