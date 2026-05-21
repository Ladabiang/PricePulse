import numpy as np
from sklearn.linear_model import LinearRegression


def predict_price(price_history):

    if len(price_history) < 2:
        return {
            "prediction": price_history[-1] if price_history else 0,
            "advice": "Not enough data"
        }

    X = np.array(range(len(price_history))).reshape(-1, 1)
    y = np.array(price_history)

    model = LinearRegression()
    model.fit(X, y)

    next_day = np.array([[len(price_history)]])
    predicted_price = int(model.predict(next_day)[0])

    current_price = price_history[-1]

    if predicted_price < current_price:
        advice = "Wait - Price may drop"
    elif predicted_price > current_price:
        advice = "Buy Now - Price may rise"
    else:
        advice = "Stable Price"

    return {
        "prediction": predicted_price,
        "advice": advice
    }