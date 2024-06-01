import pandas as pd
import matplotlib.pyplot as plt

from portfolio_tracker.core import compute_portfolio_returns_over_time


def plot_portfolio_returns(portfolio_order_df, start_date, book_currency, title, sheet):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111)
    portfolio_returns = compute_portfolio_returns_over_time(portfolio_order_df, book_currency)
    cumulative_returns = (1 + portfolio_returns).cumprod().shift(1)
    cumulative_returns.iloc[0] = 1
    mask = pd.to_datetime(cumulative_returns.index) >= start_date
    cumulative_returns[mask].plot(ax=ax)
    ax.set_title(title)
    sheet.pictures.add(fig, name=title, update=True)


def plot_donut_chart(labels, sizes, title, sheet):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)

    # Create a pie chart
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)

    # Draw a circle at the center of pie chart
    centre_circle = plt.Circle((0, 0), 0.70, fc="white")
    ax.add_artist(centre_circle)

    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis("equal")
    ax.set_title(title)
    sheet.pictures.add(fig, name=title, update=True)


def plot_sankey_diagram(budget_history_df, sheet):
    raise NotImplementedError
