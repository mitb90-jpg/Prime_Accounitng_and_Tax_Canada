import streamlit as st
import pandas as pd
import io
import pdfplumber

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

uploaded_file = st.sidebar.file_uploader(
    "Upload File (Excel or PDF)",
    type=["xlsx", "pdf"]
)

# ================= MAIN =================
if uploaded_file is not None:

    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "xlsx":
        df = pd.read_excel(uploaded_file)

    elif file_type == "pdf":
        import pdfplumber

        all_rows = []

        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:

                table = page.extract_table(
                    {
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines"
                    }
                )

                if table:
                    for row in table:

                        row_text = " ".join(str(x) for x in row if x)

                        # remove repeated headers
                        if "Date" in row_text and "Description" in row_text:
                            continue

                        all_rows.append(row)


        df = pd.DataFrame(all_rows)

        # Remove empty columns
        df = df.dropna(axis=1, how="all")

        # Assign bank statement columns
        df.columns = [
            "Date",
            "Description",
            "Withdrawals/Debits",
            "Deposits/Credits",
            "Balance"
        ]

    # ---------------- CLEAN ----------------
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace(r"\s*\(\$\)", "", regex=True)
    )

    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(how="all")


    # ---------------- FIX PDF HEADERS ----------------

    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", " ", regex=False)
        .str.strip()
    )

    for col in df.columns:
        if "Deposits" in col:
            df.rename(columns={col: "Deposits/Credits"}, inplace=True)

        if "Withdrawals" in col:
            df.rename(columns={col: "Withdrawals/Debits"}, inplace=True)

    st.write("PDF Columns:", df.columns.tolist())


    # ---------------- NORMALIZE COLUMNS ----------------
    # Make PDF columns behave like Excel columns

    if "Deposits/Credits" in df.columns:
        df["Credit"] = df["Deposits/Credits"]

    if "Withdrawals/Debits" in df.columns:
        df["Debit"] = df["Withdrawals/Debits"]


    # Convert amounts to numbers
    for col in ["Credit", "Debit"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )


    df["Category"] = ""

    # ---------------- CREDIT RULES ----------------
    df.loc[
        df["Deposits/Credits"].notna() &
        df["Description"].astype(str).str.contains("MISC PAYMENT|TRANSFER FROM|DEPOSIT|DEP. FROM ANOTHER PARTY", case=False),
        "Category"
    ] = "Revenue"


    df.loc[
        df["Deposits/Credits"].notna() &
        df["Description"].astype(str).str.contains("Insurance|HEALTH/DENTAL CLAIM", case=False),
        "Category"
    ] = "Other Income"


    # ---------------- DEBIT RULES ----------------
    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.strip().str.lower().eq("misc payment"),
        "Category"
    ] = "Misc Expenses"


    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.contains("INSURANCE", case=False),
        "Category"
    ] = "Insurance"


    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.contains("Debit Memo", case=False),
        "Category"
    ] = "Ask from Customer"


    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.contains("LOANS", case=False),
        "Category"
    ] = "Car Loan"


    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.contains("PC Bill Payment", case=False),
        "Category"
    ] = "Purchases"


    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.contains("GOODLIFE FITNESS", case=False),
        "Category"
    ] = "Personal Expenses"


    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.contains("HIGHWAY", case=False),
        "Category"
    ] = "Parking and Toll"


    df.loc[
        df["Withdrawals/Debits"].notna() &
        df["Description"].astype(str).str.contains("TSCC|POINT OF SALE PURCHASE", case=False),
        "Category"
    ] = "Vehicle Expense"


    df.loc[
        df["Withdrawals/Debits"].notna() &
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
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ---------------- CATEGORY STATUS COUNT ----------------
    total_entries = len(df)
    categorized_entries = df["Category"].astype(str).str.strip().ne("").sum()
    uncategorized_entries = total_entries - categorized_entries

    st.markdown("### 📌 Categorization Summary")
    st.markdown(f"""
    - ✅ **Total Transactions:** {total_entries:,}
    - 🟢 **Categorized Transactions:** {categorized_entries:,}
    - ⚪ **Uncategorized Transactions:** {uncategorized_entries:,}
    """)

    # ---------------- EXPORT TRANSACTIONS ----------------
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    output.seek(0)

    st.download_button(
        "⬇️ Export Categorized Data",
        data=output,
        file_name="Auto_Categorized_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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

    # ---------------- P&L EXPORT ----------------
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
    summary = df.groupby("Category")[["Credit", "Debit"]].sum().fillna(0).reset_index()

    display_summary = summary.copy()
    for col in ["Credit", "Debit"]:
        display_summary[col] = display_summary[col].apply(format_amount)

    st.subheader("📋 Category Summary")
    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    # ---------------- SUMMARY EXPORT ----------------
    summary_output = io.BytesIO()
    with pd.ExcelWriter(summary_output, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False, sheet_name="Category Summary")

    summary_output.seek(0)

    st.download_button(
        "⬇️ Export Summary Data",
        data=summary_output,
        file_name="Category_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:

    st.markdown("""
    <div style="
        background-color:#f8f9fa;
        padding:40px;
        border-radius:15px;
        text-align:center;
        border:1px solid #e0e0e0;
    ">

    <h1 style="color:#1f4e79;">
    📊 Prime Automated Categorization & Reporting System
    </h1>

    <h3 style="color:gray;">
    Prime Accounting and Tax
    </h3>

    <p style="font-size:18px;">
    Upload a bank statement or credit card statement to automatically:
    </p>

    <p style="font-size:17px;">
    ✅ Categorize Transactions<br>
    ✅ Generate Category Summary<br>
    ✅ Create Profit & Loss Statement<br>
    ✅ Export Professional Excel Reports
    </p>

    <br>

    <p style="color:#1f4e79;font-size:18px;font-weight:bold;">
    ⬅ Upload your Excel file from the sidebar to begin
    </p>

    </div>
    """, unsafe_allow_html=True)
