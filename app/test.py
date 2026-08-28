import os
from dotenv import load_dotenv
from anthropic import Anthropic
from app.discovery import discover_urls
from app.fetch import fetch_pages
from app.extract import call_extraction

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

candidates = discover_urls("toloka.vc")
pages = fetch_pages(candidates, "toloka.vc")

portfolio_page = next(p for p in pages if "portfolio" in str(p.final_url))
result = call_extraction(client, portfolio_page)
print(result)