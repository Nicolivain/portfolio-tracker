import xlwings as xw
from portfolio_tracker.run import main

if __name__ == "__main__":
    xw.Book("main.xlsm").set_mock_caller()
    main()
