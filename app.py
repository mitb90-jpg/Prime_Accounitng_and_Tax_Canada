import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Transaction Categorizer",
    page_icon="📊",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
    <style>
    .export-box {
        background-color: #1f4e79;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
    }

    .export-title {
        color: white;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
    }

    div.stDownloadButton > button {
        background-color: #ffffff;
        color: #1f4e79;
        font-weight: bold;
        padding: 0.6em 1.2em;
        border-radius: 8px;
        border: none;
        transition: 0.3s;
    }

    div.stDownloadButton > button:hover {
        background-color: #e6f0ff;
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
        "<h1 style='color:#1f4e79; font-size:42px; font-weight:bold;'>Prime Accounting and Tax</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='font-size:30px; color:gray;'>World Eyewear</p>",
        unsafe_allow_html=True
    )

# ---------------- SIDEBAR ----------------
company = st.sidebar.selectbox(
    "Select Account",
    ["Scotia Bank", "Triangle Master Card", "Visa - 6023", "Visa - 7866"]
)

st.sidebar.markdown(f"**Selected:** {company}")

uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

# ================= MAIN =================
if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    # ---------------- CLEAN ----------------
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(how="all")

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    df["Category"] = ""

    # ---------------- CREDIT RULES ----------------
    df.loc[
        df["Credit"].notna() &
        df["Description"].astype(str).str.contains(
            "MISC PAYMENT|TRANSFER FROM|DEPOSIT|DEP. FROM ANOTHER PARTY",
            case=False, na=False
        ),
        "Category"
    ] = "Revenue"

    df.loc[
        df["Credit"].notna() &
        df["Description"].astype(str).str.contains(
            "Insurance|HEALTH/DENTAL CLAIM",
            case=False, na=False
        ),
        "Category"
    ] = "Other Income"

    # ---------------- DEBIT RULES ----------------
    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("LOANS", case=False, na=False),
           "Category"] = "Car Loan"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("INSURANCE", case=False, na=False),
           "Category"] = "Insurance"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.strip().str.lower().eq("misc payment"),
           "Category"] = "Misc Expenses"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("PC Bill Payment", case=False, na=False),
           "Category"] = "Purchases"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("GOODLIFE FITNESS", case=False, na=False),
           "Category"] = "Personal Expenses"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("HIGHWAY", case=False, na=False),
           "Category"] = "Parking and Toll"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("Debit Memo", case=False, na=False),
           "Category"] = "Ask Client"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("TSCC", case=False, na=False),
           "Category"] = "Vehicle Expense"

    df.loc[df["Debit"].notna() &
           df["Description"].astype(str).str.contains("SERVICE CHARGE|Fee", case=False, na=False),
           "Category"] = "Interest and Bank charges"

    # ---------------- Sr No ----------------
    df = df.reset_index(drop=True)
    df.insert(0, "Sr. No", range(1, len(df) + 1))

    # ---------------- TABLE ----------------
    st.subheader("📊 Categorized Transactions")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ================= PROFIT & LOSS =================
    st.subheader("📊 Profit & Loss Statement")

    total_revenue = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()
    expense_df = df[df["Category"] != "Revenue"]

    expense_summary = expense_df.groupby("Category")["Debit"].sum().reset_index()
    expense_summary.columns = ["Category", "Amount"]

    total_expenses = expense_summary["Amount"].sum()
    net_profit = total_revenue - total_expenses

    pl_rows = [["Revenue", total_revenue],
               ["Less: Expenses", ""]]

    for _, r in expense_summary.iterrows():
        pl_rows.append([r["Category"], r["Amount"]])

    pl_rows += [["Total Expenses", total_expenses],
                ["Net Profit", net_profit]]

    pl_df = pd.DataFrame(pl_rows, columns=["Description", "Amount"])

    st.dataframe(pl_df, use_container_width=True, hide_index=True)

    # ================= CREATE P&L FILE =================
    pl_output = io.BytesIO()
    with pd.ExcelWriter(pl_output, engine="openpyxl") as writer:
        pl_df.to_excel(writer, index=False, sheet_name="Profit & Loss")
    pl_output.seek(0)

# ---------------- CREATE P&L EXPORT ----------------
pl_output = io.BytesIO()

with pd.ExcelWriter(pl_output, engine="openpyxl") as writer:
    pl_df.to_excel(writer, index=False, sheet_name="Profit & Loss")

pl_output.seek(0)

# ---------------- EXPORT BOX (CLICK FEEL UI) ----------------
st.markdown("""
<div class="export-box">
    <div class="export-title">📊 Export Profit & Loss Statement</div>
</div>
""", unsafe_allow_html=True)

st.download_button(
    label="📥 Click to Export Profit & Loss",
    data=pl_output,
    file_name="Profit_and_Loss.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

    # ================= CATEGORY SUMMARY =================
    amounts = df.groupby("Category")[["Credit", "Debit"]].sum()
    amounts["Net"] = amounts["Credit"].fillna(0) + amounts["Debit"].fillna(0)

    summary_df = amounts.reset_index()[["Category", "Net"]]

    st.subheader("📋 Category Summary")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # ================= MAIN EXPORT =================
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    output.seek(0)

    st.markdown("""
    <div class="export-box">
        <div class="export-title">📤 Export Categorized Data</div>
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        "⬇️ Download Excel File",
        data=output,
        file_name="Auto_categorised_file.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload an Excel file to begin.")
