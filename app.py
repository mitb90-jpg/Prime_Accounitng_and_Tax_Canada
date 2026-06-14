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

# ---------------- CLIENT SELECTION ----------------
client = st.sidebar.selectbox(
    "Select Statement",
    [
        "Scotia_Bank",
        "Triangle_Master_Card",
        "Visa_card_6023",
        "Visa_card_7866"
    ]
)

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# ---------------- MAIN APP ----------------
if uploaded_file is not None:

    # ---------------- READ DATA ----------------
    df = pd.read_excel(uploaded_file)

    # ---------------- CLEAN DATA ----------------
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(how="all")

rules_file = f"rules/{client}.xlsx"
rules_df = pd.read_excel(rules_file)

for _, rule in rules_df.iterrows():

    keyword = str(rule["Keyword"])
    category = str(rule["Category"])

    df.loc[
        df["Description"].astype(str).str.contains(keyword, case=False, na=False),
        "Category"
    ] = category

    # ---------------- DATE FIX ----------------
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    # ---------------- CATEGORY COLUMN ----------------
    df["Category"] = ""

    # ---------------- APPLY RULES ----------------
    for _, rule in rules_df.iterrows():

        keyword = str(rule["Keyword"])
        category = str(rule["Category"])

        df.loc[
            df["Description"].astype(str).str.contains(keyword, case=False, na=False),
            "Category"
        ] = category

    # ---------------- ADD SERIAL NUMBER ----------------
    df = df.reset_index(drop=True)
    df.insert(0, "Sr. No", range(1, len(df) + 1))

    # ---------------- TABLE ----------------
    st.subheader("📊 Categorized Transactions")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ---------------- SUMMARY ----------------
    revenue = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()
    investment = df.loc[df["Category"] == "Investment income", "Debit"].fillna(0).sum()
    loan = df.loc[df["Category"] == "Loan to world eyewear", "Debit"].fillna(0).sum()
    bank_charges = df.loc[df["Category"] == "Interest and Bank charges", "Debit"].fillna(0).sum()

    st.subheader("📊 Summary Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", revenue)
    c2.metric("Investment", investment)
    c3.metric("Loans", loan)
    c4.metric("Bank Charges", bank_charges)

    # ---------------- PIE CHART ----------------
    data = {
        "Revenue": revenue,
        "Investment": investment,
        "Loan": loan,
        "Bank Charges": bank_charges
    }

    data = {k: v for k, v in data.items() if v > 0}

    if data:
        fig, ax = plt.subplots()
        ax.pie(data.values(), labels=data.keys(), autopct="%1.1f%%")
        ax.set_title("Financial Distribution")
        st.pyplot(fig)

    # ---------------- SUMMARY TABLE ----------------
    st.subheader("📋 Category Summary")

    summary_df = pd.DataFrame({
        "Category": list(data.keys()),
        "Amount": [f"${v:,.2f}" for v in data.values()]
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
        file_name="Auto_categorised_file.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload an Excel file to begin.")
