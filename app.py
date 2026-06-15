import streamlit as st
import pandas as pd
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Transaction Categorizer",
    page_icon="📊",
    layout="wide"
)

# ---------------- FORMAT FUNCTION ----------------
def format_amount(x):
    try:
        if pd.isna(x):
            return ""
        if isinstance(x, (int, float)):
            return f"{x:,.2f}"
        return x
    except:
        return x

# ---------------- CSS ----------------
st.markdown("""
<style>
div.stDownloadButton > button {
    width: 100%;
    background-color: #1f4e79;
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 12px;
    border-radius: 10px;
}
div.stDownloadButton > button:hover {
    background-color: #163a5c;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col1, col2 = st.columns([1, 6])

with col1:
    st.image("Logo.jpeg", width=100)

with col2:
    st.markdown("<h1 style='color:#1f4e79;'>Prime Accounting and Tax</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:20px; color:gray;'>World Eyewear</p>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
company = st.sidebar.selectbox(
    "Select Account",
    ["Scotia Bank", "Triangle Master Card", "Visa - 6023", "Visa - 7866"]
)

uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

# ================= MAIN =================
if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    # ---------------- CLEAN (FIXED UNNAMED COLUMN HERE) ----------------
    df.columns = df.columns.astype(str).str.strip()

    # ✅ REMOVE UNNAMED COLUMNS (FINAL FIX)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

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

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("LOANS", case=False),
        "Category"
    ] = "Car Loan"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("PC Bill Payment", case=False),
        "Category"
    ] = "Purchases"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("GOODLIFE FITNESS", case=False),
        "Category"
    ] = "Personal Expenses"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("HIGHWAY", case=False),
        "Category"
    ] = "Parking and Toll"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("SERVICE CHARGE|FEE", case=False),
        "Category"
    ] = "Interest and Bank charges"

    # ---------------- Sr No ----------------
    df = df.reset_index(drop=True)
    df.insert(0, "Sr. No", range(1, len(df) + 1))

    # ---------------- DISPLAY TABLE ----------------
    display_df = df.copy()

    for col in ["Credit", "Debit"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_amount)

    st.subheader("📊 Categorized Transactions")
    st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

    # ---------------- PROFIT & LOSS ----------------
    st.subheader("📊 Profit & Loss Statement")

    revenue = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()
    expense_df = df[df["Category"] != "Revenue"]
    expense_summary = expense_df.groupby("Category")["Debit"].sum().reset_index()

    total_expenses = expense_summary["Debit"].sum()
    net_profit = revenue - total_expenses

    pl_rows = [["Revenue", revenue], ["Less: Expenses", ""]]

    for _, r in expense_summary.iterrows():
        pl_rows.append([r["Category"], r["Debit"]])

    pl_rows += [["Total Expenses", total_expenses],
                ["Net Profit", net_profit]]

    pl_df = pd.DataFrame(pl_rows, columns=["Description", "Amount"])
    pl_df["Amount"] = pl_df["Amount"].apply(format_amount)

    st.dataframe(pl_df, use_container_width=True, hide_index=True)

    # ---------------- P&L DOWNLOAD ----------------
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
    summary = summary.reset_index()

    for col in ["Credit", "Debit", "Net"]:
        summary[col] = summary[col].apply(format_amount)

    st.subheader("📋 Category Summary")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # ---------------- MAIN DOWNLOAD ----------------
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

    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#1f4e79,#2e75b6);
        padding:50px;
        border-radius:20px;
        text-align:center;
        margin-top:30px;
        color:white;
    ">
        <h1>📊 Smart Transaction Categorizer</h1>

        <h3>Prime Accounting and Tax</h3>

        <p style="font-size:18px;">
            Upload an Excel file from the sidebar to generate:
        </p>

        <p style="font-size:17px;">
            📋 Category Summary<br>
            📈 Profit & Loss Statement<br>
            📤 Export Categorized Data<br>
            ⚡ Automated Transaction Classification
        </p>
    </div>
    """, unsafe_allow_html=True)
