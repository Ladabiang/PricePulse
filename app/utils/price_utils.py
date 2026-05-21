import re

def parse_price(value):
    if not value:
        return 0

    value = str(value)

    match = re.findall(r"[\d,.]+", value)

    if not match:
        return 0

    number = match[0].replace(",", "")

    try:
        return int(float(number))
    except:
        return 0


def safe_price(price):
    p = parse_price(price)

    # prevent garbage values like 1080000
    if p > 10_00_000:
        return 0

    return p