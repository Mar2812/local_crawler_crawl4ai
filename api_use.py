import time
from fastapi import FastAPI, Body
from typing import List
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from fastapi.middleware.cors import CORSMiddleware
import re

# 创建 FastAPI 实例
app = FastAPI(title="Web Crawler API", description="使用 crawl4ai 的网页爬虫 API，支持内容过滤")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- 数据模型 -----------

class CrawlRequest(BaseModel):
    urls: List[str]
    filter_threshold: float = 0.3
    threshold_type: str = "dynamic"
    min_word_threshold: int = 5
    use_fit: bool = True  # 是否使用 fit 内容过滤

class CrawlResult(BaseModel):
    url: str
    content: str = ""
    content_type: str = "raw"
    is_success: bool
    time_cost: float
    raw_length: int = 0
    fit_length: int = 0

# ----------- 全局爬虫实例 -----------

crawler: AsyncWebCrawler = None  # 会在 startup 时初始化

@app.on_event("startup")
async def startup_event():
    global crawler
    crawler = AsyncWebCrawler()
    await crawler.__aenter__()  # 手动进入异步上下文，初始化浏览器

@app.on_event("shutdown")
async def shutdown_event():
    global crawler
    if crawler:
        await crawler.__aexit__(None, None, None)  # 手动退出，关闭浏览器

# ----------- API 路由 -----------

@app.post("/crawl", response_model=List[CrawlResult])
async def crawl_urls(request: CrawlRequest = Body(...)):
    results = []

    # 创建内容过滤器和 Markdown 生成器
    prune_filter = PruningContentFilter(
        threshold=request.filter_threshold,
        threshold_type=request.threshold_type,
        min_word_threshold=request.min_word_threshold
    )
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    # 创建爬虫配置
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True,
        markdown_generator=md_generator,
        page_timeout=8000,
        semaphore_count=10,
        wait_for_images=False,
        only_text=True,
        remove_forms=True,
        remove_overlay_elements=True,
        scan_full_page=False,
        scroll_delay=0.1,
        exclude_external_links=True,
        exclude_internal_links=True,
        css_selector="body",
        excluded_selector="nav, footer, .popup, .ad-banner",
        excluded_tags=["script", "style"],
    )

    # 爬取多个 URL
    total_start_time = time.time()

    async for result in await crawler.arun_many(request.urls, config=run_conf):
        current_time = time.time()
        time_cost = current_time - result.dispatch_result.start_time

        if result.success:
            raw_md = result.markdown.raw_markdown
            fit_md = result.markdown.fit_markdown
            raw_length = len(raw_md)
            cleaned = re.sub(r'[\n-.,*]', '', fit_md)
            fit_length = len(cleaned)
            if request.use_fit and fit_length > 10:
                content = fit_md
                content_type = "fit"
            else:
                content = raw_md
                content_type = "raw"

            results.append(CrawlResult(
                url=result.url,
                content=content,
                content_type=content_type,
                is_success=True,
                time_cost=time_cost,
                raw_length=raw_length,
                fit_length=fit_length
            ))
        else:
            error_message = f"Status:Failed, 爬取失败!"
            results.append(CrawlResult(
                url=result.url,
                # content=result.error_message,
                content=error_message,
                content_type="error",
                is_success=False,
                time_cost=time_cost
            ))

    return results

# ----------- 本地启动 -----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8346)
