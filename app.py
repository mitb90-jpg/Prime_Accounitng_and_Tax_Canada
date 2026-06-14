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

col1, col2 = st.columns([1, 6])

with col1:
    st.image("WhatsApp Image 2026-06-12 at 5.22.49 PM.jpeg", width=100)

with col2:
    st.markdown(
        "<h1 style='color:#1f4e79; font-size:42px; font-weight:bold; margin-bottom:0;'>Prime Accounting and Tax</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='font-size:30px; color:gray; margin-top:0;'>2331061 Ontario Inc.</p>",
        unsafe_allow_html=True
    )

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    # ---------------- CLEAN DATA ----------------
    df.columns = df.columns.astype(str).str.strip()

    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(how="all")

    # ---------------- DATE FIX ----------------
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    # ---------------- CATEGORY COLUMN ----------------
    df["Category"] = ""

    # ---------------- CREDIT RULE ----------------
    credit_mask = (
        df["Credit"].notna() &
        df["Description"].astype(str).str.contains("Proceeds|Deposit", case=False, na=False)
    )
    df.loc[credit_mask, "Category"] = "Revenue"

    # ---------------- DEBIT RULES ----------------
    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("CHQ", na=False),
        "Category"
    ] = "Loan to world eyewear"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("TRANSFER TO", case=False, na=False),
        "Category"
    ] = "Loan to world eyewear"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("TRANSFER OTHER", case=False, na=False),
        "Category"
    ] = "Investment income"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("SERVICE CHARGE", case=False, na=False),
        "Category"
    ] = "Interest and Bank charges"

    # ---------------- ADD Sr. No ----------------
    df = df.reset_index(drop=True)
    df.insert(0, "Sr. No", range(1, len(df) + 1))

    # ---------------- FINAL TABLE ----------------
    st.subheader("📊 Categorized Transactions")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ---------------- SUMMARY ----------------
    st.subheader("📊 Summary Dashboard")

    revenue_count = (df["Category"] == "Revenue").sum()
    bank_charges_count = (df["Category"] == "Interest and Bank charges").sum()
    loan_count = (df["Category"] == "Loan to world eyewear").sum()
    investment_count = (df["Category"] == "Investment income").sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Revenue", revenue_count)
    col2.metric("Bank Charges", bank_charges_count)
    col3.metric("Loans", loan_count)
    col4.metric("Investment", investment_count)

    # ---------------- AMOUNTS ----------------
    revenue_amount = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()
    investment_amount = df.loc[df["Category"] == "Investment income", "Debit"].fillna(0).sum()
    bank_charge_amount = df.loc[df["Category"] == "Interest and Bank charges", "Debit"].fillna(0).sum()
    loan_amount = df.loc[df["Category"] == "Loan to world eyewear", "Debit"].fillna(0).sum()

    # ---------------- PIE CHART ----------------
    st.subheader("🥧 Financial Distribution")

    amounts = {
        "Revenue": revenue_amount,
        "Investment": investment_amount,
        "Loan": loan_amount,
        "Bank Charges": bank_charge_amount
    }

    amounts = {k: v for k, v in amounts.items() if v > 0}

    if amounts:
        fig, ax = plt.subplots()
        ax.pie(amounts.values(), labels=amounts.keys(), autopct="%1.1f%%")
        ax.set_title("Financial Distribution")
        st.pyplot(fig)

    # ---------------- SUMMARY TABLE ----------------
    st.subheader("📋 Category Summary")

    summary_df = pd.DataFrame({
        "Category": list(amounts.keys()),
        "Amount": [f"${v:,.2f}" for v in amounts.values()]
    })

    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # ---------------- DOWNLOAD ----------------
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")

    output.seek(0)

    st.download_button(
        "⬇️ Download Excel File",
        data=output,
        file_name="Auto_categorised_file_2331061_Ontario_Inc.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload an Excel file to begin.")
