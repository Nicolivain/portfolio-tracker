from constant import BudgettingColumns
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import xlwings as xw
from utils import read_table

def preprocess_budget_data(df: pd.DataFrame) -> pd.DataFrame:
    # Convert types
    df[BudgettingColumns.date.value] = pd.to_datetime(df[BudgettingColumns.date.value], infer_datetime_format=True)

    df[BudgettingColumns.receiver.value] = df[BudgettingColumns.receiver.value].astype(str)
    df[BudgettingColumns.category.value] = df[BudgettingColumns.category.value].astype(str)
    df[BudgettingColumns.subcategory.value] = df[BudgettingColumns.subcategory.value].astype(str)
    df[BudgettingColumns.notes.value] = df[BudgettingColumns.notes.value].astype(str)
    df[BudgettingColumns.description.value] = df[BudgettingColumns.description.value].astype(str)
    df[BudgettingColumns.account.value] = df[BudgettingColumns.account.value].astype(str)
    df[BudgettingColumns.bank.value] = df[BudgettingColumns.bank.value].astype(str)

    # Convert BudgettingColumns.amount.value column to numeric after removing the space
    df[BudgettingColumns.amount.value] = pd.to_numeric(df[BudgettingColumns.amount.value].str.replace(' ', '').str.replace(',', '.'))

    return df

def get_income(budget_history_df, window=None):    
    income = budget_history_df[budget_history_df[BudgettingColumns.amount.value] > 0]
    if window:
        start, end = pd.to_datetime(window[0]), pd.to_datetime(window[1])
        return income[(income[BudgettingColumns.date.value] > start) & (income[BudgettingColumns.date.value] < end)]
    else:
        return income

def get_expenses(budget_history_df, window=None):
    expenses = budget_history_df[budget_history_df[BudgettingColumns.amount.value] < 0]
    if window:
        start, end = pd.to_datetime(window[0]), pd.to_datetime(window[1])
        return expenses[(expenses[BudgettingColumns.date.value] > start) & (expenses[BudgettingColumns.date.value] < end)]
    else:
        return expenses
    
def plot_income_category(income, sheet, subcategory=False):

    # Remove rows where supplierFound value contain both 'antoine' and 'toffano'
    income = income[~income[BudgettingColumns.receiver.value].str.contains('antoine toffano')]
    # Remove all columns but subcategory, category and amount
    income = income[[BudgettingColumns.subcategory.value, BudgettingColumns.category.value, BudgettingColumns.amount.value]]
    # Convert income to positive values
    income[BudgettingColumns.amount.value] = income[BudgettingColumns.amount.value].abs()   
    
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    if subcategory:
        grouped = income.groupby(BudgettingColumns.subcategory.value)[BudgettingColumns.amount.value].sum()
    else:
        grouped = income.groupby(BudgettingColumns.category.value)[BudgettingColumns.amount.value].sum()

    grouped.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=190, pctdistance=0.9, labeldistance=1.15, radius=0.8, wedgeprops=dict(width=0.3, edgecolor='w'))

    # Spread textual labels
    ax.set_title("Income by Subcategory" if subcategory else "Income by Category", fontsize=16, fontweight='bold')
    ax.set_ylabel('')  # Hide the y-axis label
    ax.legend(bbox_to_anchor=(1, 1), loc='upper left')  # Move the legend outside the pie chart

    sheet.pictures.add(fig, name="Income by Subcategory" if subcategory else "Income by Category", update=True)

def plot_expenses_category(expenses, sheet, subcategory=False):

    # Remove rows where supplierFound value contain both 'antoine' and 'toffano'
    expenses = expenses[~expenses[BudgettingColumns.receiver.value].str.contains('antoine toffano')]
    # Remove all columns but subcategory, category and amount
    expenses = expenses[[BudgettingColumns.subcategory.value, BudgettingColumns.category.value, BudgettingColumns.amount.value]]
    # Convert expenses to positive values
    expenses[BudgettingColumns.amount.value] = expenses[BudgettingColumns.amount.value].abs()   
    
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    if subcategory:
        grouped = expenses.groupby(BudgettingColumns.subcategory.value)[BudgettingColumns.amount.value].sum()
    else:
        grouped = expenses.groupby(BudgettingColumns.category.value)[BudgettingColumns.amount.value].sum()
    grouped.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=190, pctdistance=0.9, labeldistance=1.15, radius=0.8, wedgeprops=dict(width=0.3, edgecolor='w'))

    # Spread textual labels
    ax.set_title("Expenses by Subcategory" if subcategory else "Expenses by Category", fontsize=16, fontweight='bold')
    ax.set_ylabel('')  # Hide the y-axis label
    ax.legend(bbox_to_anchor=(1, 1), loc='upper left')  # Move the legend outside the pie chart

    sheet.pictures.add(fig, name="Expenses by Subcategory" if subcategory else "Expenses by Category", update=True)
    
def plot_evolving_balance(budget_history_df, sheet):
    budget_history_df = budget_history_df.sort_values(by=BudgettingColumns.date.value)
    budget_history_df['cumulative'] = budget_history_df[BudgettingColumns.amount.value].cumsum()
    
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    
    budget_history_df.plot(x=BudgettingColumns.date.value, y='cumulative', ax=ax)
    
    ax.set_title("Evolving Balance", fontsize=16, fontweight='bold')
    ax.set_ylabel('Balance')
    ax.set_xlabel('Date')
    
    sheet.pictures.add(fig, name="Evolving Balance", update=True)

def plot_sankey(budget_history_df, sheet):
    # Create a new column 'amount_type' that indicates whether the amount is positive or negative
    budget_history_df['amount_type'] = ['income' if x > 0 else 'expenses' for x in budget_history_df[BudgettingColumns.amount.value]]

    # Create a new column 'abs_amount' that contains the absolute value of 'amount'
    budget_history_df['abs_amount'] = budget_history_df[BudgettingColumns.amount.value].abs()

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=budget_history_df[BudgettingColumns.subcategory.value].tolist() + budget_history_df[BudgettingColumns.category.value].tolist() + budget_history_df['amount_type'].tolist(),
            color="blue"
        ),
        link=dict(
            source=budget_history_df[BudgettingColumns.subcategory.value].apply(lambda x: budget_history_df[BudgettingColumns.subcategory.value].tolist().index(x)),
            target=budget_history_df[BudgettingColumns.category.value].apply(lambda x: budget_history_df[BudgettingColumns.category.value].tolist().index(x)),
            value=budget_history_df['abs_amount']
        )
    )])

    fig.update_layout(title_text="Sankey Diagram of Budget History", font_size=10)
    sheet.pictures.add(fig, name="Sankey Diagram of Budget History", update=True)


def update_budget():
    wb = xw.Book.caller()
    budget_sheet = wb.sheets["Budget"]
    budget_history_df = read_table("B2", budget_sheet, index=0, header=1)
    budget_history_df = preprocess_budget_data(budget_history_df)
    
    # Get value of dropdown menu on cell 'O2'
    window = budget_sheet.range("O2").value
    # Set color to gay, text color as white
    budget_sheet.range("O2").color = (192, 192, 192)
    budget_sheet.range("O2").api.Font.Color = -1
    match window:
        case 'All time':
            window = None
        case 'Last 30 days':
            window = (pd.Timestamp.now() - pd.DateOffset(days=30), pd.Timestamp.now())
        case 'Last 90 days':
            window = (pd.Timestamp.now() - pd.DateOffset(days=90), pd.Timestamp.now())
        case 'Last 180 days':
            window = (pd.Timestamp.now() - pd.DateOffset(days=180), pd.Timestamp.now())
        case 'Last 365 days':
            window = (pd.Timestamp.now() - pd.DateOffset(days=365), pd.Timestamp.now())
        case 'Year to date':
            window = (pd.Timestamp.now().replace(month=1, day=1), pd.Timestamp.now())
        case _:
            window = None

    # Write the budget history size to the sheet
    income = get_income(budget_history_df, window=window)
    expenses = get_expenses(budget_history_df, window=window)

    # Write summary statistics to the sheet
    budget_sheet.range("O4").value = 'Income'
    budget_sheet.range("O5").value = income[BudgettingColumns.amount.value].sum()
    budget_sheet.range("P4").value = 'Expenses'
    budget_sheet.range("P5").value = expenses[BudgettingColumns.amount.value].sum()
    budget_sheet.range("Q4").value, budget_sheet.range("Q4").color = 'Net', (192, 192, 192)
    budget_sheet.range("Q5").value = budget_sheet.range("O5").value + budget_sheet.range("P5").value

    # Color Summary Statistics cells as  green/red and net based on value
    budget_sheet.range("O4").color, budget_sheet.range("O5").color = (0, 255, 0), (0, 255, 0)
    budget_sheet.range("P4").color, budget_sheet.range("P5").color = (255, 0, 0), (255, 0, 0)
    budget_sheet.range("Q5").color = (0, 255, 0) if budget_sheet.range("Q5").value > 0 else (255, 0, 0)

    plot_income_category(
        income,
        budget_sheet
    )
    plot_income_category(
        income,
        budget_sheet,
        subcategory=True
    )
    plot_expenses_category(
        expenses,
        budget_sheet
    )
    plot_expenses_category(
        expenses,
        budget_sheet,
        subcategory=True
    )