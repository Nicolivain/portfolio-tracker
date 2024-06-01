import xlwings as xw
from portfolio_tracker.run import main

if __name__ == "__main__":

    books = {
        "UK_BOOK": "GBP",
        "US_BOOK": "USD",
        "EU_BOOK": "EUR"
    }

    xw.Book("main.xlsm").set_mock_caller()
    main(books)
