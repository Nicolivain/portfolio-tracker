import xlwings as xw
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog

from portfolio_tracker.constant import BudgettingColumns
from portfolio_tracker.utils import read_table
from portfolio_tracker.budget_utils import (
    get_income,
    get_expenses,
    plot_income_category,
    plot_expenses_category,
    preprocess_budget_data,
)


def import_csv():
    wb = xw.Book.caller()
    budget_sheet = wb.sheets["Budget"]
    df = read_csv()

    existing_data = read_table("B2", budget_sheet, index=0, header=1)

    # Directly write to sheet if no previous data
    if existing_data.shape[1] == 1:
        budget_sheet.range("B2").options(index=False).value = df
        return

    df.columns = existing_data.columns
    df = pd.concat([existing_data, df], ignore_index=True).drop_duplicates(keep="first")
    df = df.where(pd.notnull(df), None)
    # Delete existing data and write the new data
    budget_sheet.range("B2").expand().delete()
    budget_sheet.range("B2").options(index=False).value = df


def read_csv():
    root = tk.Tk()
    root.withdraw()

    # Open a file dialog
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])

    # Read the first line of the file and derive the separator and colnames
    with open(file_path, "r") as f:
        first_line = f.readline()
        if first_line.count(",") > first_line.count(";"):
            sep = ","
        else:
            sep = ";"

    df = pd.read_csv(file_path, sep=sep)

    return df
