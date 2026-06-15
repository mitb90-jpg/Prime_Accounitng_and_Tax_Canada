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

# ---------------- COMPANY SELECTION ----------------
company = st.sidebar.selectbox(
    "Select Account",
    [
        "Scotia Bank",
        "Triangle Master Card",
        "Visa - 6023",
        "Visa - 7866"
    ]
)

st.sidebar.markdown(f"**Selected:** {company}")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# ---------------- MAIN LOGIC ----------------
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
    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("LOANS", case=False, na=False),
        "Category"
    ] = "Car Loan"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("INSURANCE", case=False, na=False),
        "Category"
    ] = "Insurance"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.strip().str.lower().eq("misc payment"),
        "Category"
    ] = "Misc Expenses"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("PC Bill Payment", case=False, na=False),
        "Category"
    ] = "Purchases"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("GOODLIFE FITNESS", case=False, na=False),
        "Category"
    ] = "Personal Expenses"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("HIGHWAY", case=False, na=False),
        "Category"
    ] = "Parking and Toll"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("Debit Memo", case=False, na=False),
        "Category"
    ] = "Ask Client"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("TSCC", case=False, na=False),
        "Category"
    ] = "Vehicle Expense"

    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("SERVICE CHARGE|Fee", case=False, na=False),
        "Category"
    ] = "Interest and Bank charges"

    # ---------------- Sr No ----------------
    df = df.reset_index(drop=True)
    df.insert(0, "Sr. No", range(1, len(df) + 1))

    # ---------------- TABLE ----------------
    st.subheader("📊 Categorized Transactions")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ---------------- PROFIT & LOSS ----------------
    st.subheader("📊 Profit & Loss Statement")

    total_revenue = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()

    expense_df = df[df["Category"] != "Revenue"]

    expense_summary = expense_df.groupby("Category")["Debit"].sum().reset_index()
    expense_summary.columns = ["Category", "Amount"]

    total_expenses = expense_summary["Amount"].sum()

    net_profit = total_revenue - total_expenses

    pl_data = []
    pl_data.append(["Revenue", total_revenue])
    pl_data.append(["Less: Expenses", ""])

    for _, row in expense_summary.iterrows():
        pl_data.append([row["Category"], row["Amount"]])

    pl_data.append(["Total Expenses", total_expenses])
    pl_data.append(["Net Profit", net_profit])

    pl_df = pd.DataFrame(pl_data, columns=["Description", "Amount"])

    pl_df["Amount"] = pl_df["Amount"].apply(
        lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x
    )

    st.dataframe(pl_df, use_container_width=True, hide_index=True)

    # ---------------- FULL AMOUNTS BLOCK ----------------
    revenue_amount = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()
    other_income_amount = df.loc[df["Category"] == "Other Income", "Credit"].fillna(0).sum()

    associates_opticians_amount = df.loc[df["Category"] == "Associates & Opticians", "Debit"].fillna(0).sum()
    car_loan_amount = df.loc[df["Category"] == "Car Loan", "Debit"].fillna(0).sum()
    cdn_tire_options_mc_amount = df.loc[df["Category"] == "Cdn Tire Options MC", "Debit"].fillna(0).sum()
    drawings_amount = df.loc[df["Category"] == "Drawings", "Debit"].fillna(0).sum()
    erin_mills_optical_amount = df.loc[df["Category"] == "Erin Mills Optical", "Debit"].fillna(0).sum()
    insurance_amount = df.loc[df["Category"] == "Insurance", "Debit"].fillna(0).sum()
    legal_and_professional_fee_amount = df.loc[df["Category"] == "Legal and professional fee", "Debit"].fillna(0).sum()
    misc_expenses_amount = df.loc[df["Category"] == "Misc Expenses", "Debit"].fillna(0).sum()
    interest_and_bank_charges_amount = df.loc[df["Category"] == "Interest and Bank charges", "Debit"].fillna(0).sum()
    parking_and_toll_amount = df.loc[df["Category"] == "Parking and Toll", "Debit"].fillna(0).sum()
    personal_expense_amount = df.loc[df["Category"] == "Personal Expenses", "Debit"].fillna(0).sum()
    purchases_amount = df.loc[df["Category"] == "Purchases", "Debit"].fillna(0).sum()
    repairs_and_maintenance_amount = df.loc[df["Category"] == "Repairs and Maintenance", "Debit"].fillna(0).sum()
    vehicle_expense_amount = df.loc[df["Category"] == "Vehicle Expense", "Debit"].fillna(0).sum()

    # ---------------- CATEGORY SUMMARY ----------------
    amounts = {
        "Revenue": revenue_amount,
        "Other Income": other_income_amount,
        "Associates & Opticians": associates_opticians_amount,
        "Car Loan": car_loan_amount,
        "Cdn Tire Options MC": cdn_tire_options_mc_amount,
        "Drawings": drawings_amount,
        "Erin Mills Optical": erin_mills_optical_amount,
        "Insurance": insurance_amount,
        "Legal and Professional Fee": legal_and_professional_fee_amount,
        "Misc Expenses": misc_expenses_amount,
        "Interest and Bank Charges": interest_and_bank_charges_amount,
        "Parking and Toll": parking_and_toll_amount,
        "Personal Expenses": personal_expense_amount,
        "Purchases": purchases_amount,
        "Repairs and Maintenance": repairs_and_maintenance_amount,
        "Vehicle Expense": vehicle_expense_amount
    }

    amounts = {k: v for k, v in amounts.items() if v != 0}

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
        file_name="Auto_categorised_file.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload an Excel file to begin.")

# ---------------- DOWNLOAD PROFIT & LOSS ----------------
output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    pl_df.to_excel(writer, index=False, sheet_name="Profit & Loss")

output.seek(0)

st.download_button(
    "⬇️ Download Profit & Loss Statement",
    data=output,
    file_name="Profit_and_Loss.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
