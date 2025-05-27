# utils.py

import os

def save_screenshot(driver, index):
    filename = f"{index}.png"
    directory = "screenshots"
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    driver.save_screenshot(path)
    return filename
