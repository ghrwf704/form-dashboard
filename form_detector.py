from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
from utils import save_screenshot  # スクリーンショット保存用関数

def extract_meta_tags(html):
    soup = BeautifulSoup(html, "html.parser")
    description = soup.find("meta", attrs={"name": "description"})
    keywords = soup.find("meta", attrs={"name": "keywords"})

    return {
        "meta_description": description["content"].strip() if description and description.get("content") else "",
        "meta_keywords": keywords["content"].strip() if keywords and keywords.get("content") else ""
    }

def capture_form_info(driver, form, index):
    try:
        inputs = form.find_elements(By.TAG_NAME, "input")
        textareas = form.find_elements(By.TAG_NAME, "textarea")
        field_names = []

        for field in inputs + textareas:
            name = field.get_attribute("name")
            if name:
                field_names.append(name)

        # フォーム情報取得のみ（送信は行わない）
        screenshot_filename = save_screenshot(driver, index + 1)
        meta_info = extract_meta_tags(driver.page_source)

        return {
            "field_names": field_names,
            "status": "form_found",
            "error": "",
            "screenshot": screenshot_filename,
            "meta_description": meta_info["meta_description"],
            "meta_keywords": meta_info["meta_keywords"]
        }

    except Exception as e:
        return {
            "field_names": [],
            "status": "error",
            "error": str(e),
            "screenshot": "",
            "meta_description": "",
            "meta_keywords": ""
        }

def detect_forms(driver):
    forms = driver.find_elements(By.TAG_NAME, "form")
    results = []

    for index, form in enumerate(forms):
        info = capture_form_info(driver, form, index)
        results.append(info)

    return results
