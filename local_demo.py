import asyncio
import time
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

def read_urls_from_file(filepath):
    with open(filepath, 'r') as file:
        return [line.strip() for line in file if line.strip()]

async def quick_parallel_example():
    urls = ["https://zhuanlan.zhihu.com/p/1896508930198324676"]
    # urls = read_urls_from_file("/mnt/data/crawl4ai/urls.txt")

    # 设置内容过滤器和 Markdown 生成器
    prune_filter = PruningContentFilter(
        threshold=0.45,
        threshold_type="dynamic",
        min_word_threshold=5
    )
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True,
        markdown_generator=md_generator
    )

    output_dir = "/mnt/data/crawl4ai/outputs"
    os.makedirs(output_dir, exist_ok=True)

    start_time = time.time()

    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun_many(urls, config=run_conf):
            if result.success:
                print(f"[OK] {result.url}")
                print(f"    Raw Markdown length: {len(result.markdown.raw_markdown)}")
                print(f"    Fit Markdown length: {(result.markdown.fit_markdown)}")

                # 生成安全文件名
                filename = result.url.replace("https://", "").replace("http://", "").replace("/", "_")
                raw_path = os.path.join(output_dir, f"{filename}_raw.txt")
                fit_path = os.path.join(output_dir, f"{filename}_fit.txt")

                # 保存 Markdown 内容到文件
                # with open(raw_path, "w", encoding="utf-8") as f:
                #     f.write(result.markdown.raw_markdown)

                # with open(fit_path, "w", encoding="utf-8") as f:
                #     f.write(result.markdown.fit_markdown)

            else:
                print(f"[ERROR] {result.url} => {result.error_message}")

    total_time = time.time() - start_time
    print(f"\n[INFO] Total crawl time: {total_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(quick_parallel_example())
