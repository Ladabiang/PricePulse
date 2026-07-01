import numpy as np
from sklearn.linear_model import LinearRegression


def predict_next_price(history_data):
    if not history_data or len(history_data) < 2:
        return None

    prices = []

    for item in history_data:
        price = float(item.get("price") or 0)
        if price > 0:
            prices.append(price)

    if len(prices) < 2:
        return None

    days = np.arange(1, len(prices) + 1).reshape(-1, 1)
    prices_array = np.array(prices)

    model = LinearRegression()
    model.fit(days, prices_array)

    next_day = np.array([[len(prices) + 1]])
    predicted_price = model.predict(next_day)[0]

    return round(float(predicted_price), 2)