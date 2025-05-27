from search_engine import bing_search

def main():
    query = "お問い合わせ site:.jp"  # 検索キーワード
    max_pages = 3  # 最大検索ページ数（1ページあたり約10件）
    output_file = "urls_raw.txt"

    print(f"🔍 Bing検索開始:「{query}」 ({max_pages}ページ分)")
    urls = bing_search(query, max_pages)

    if not urls:
        print("⚠ URLが取得できませんでした。")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

    print(f"✅ {len(urls)} 件のURLを {output_file} に保存しました。")

if __name__ == "__main__":
    main()
