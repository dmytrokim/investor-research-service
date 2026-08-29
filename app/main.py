from anthropic import Anthropic
from dotenv import load_dotenv
from app import config
import os
from app.extract import build_investor_profile, call_extraction, apply_post_filter, call_strategy
from app.fetch import fetch_pages
from app.discovery import normalize_domain
from app.quality_valid import is_empty_page, count_titles
from app.gen_brief import render_brief

def main():
    load_dotenv()
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    investor_name = input("Enter the investor name: ").strip()
    if not investor_name:
        print("Error: investor name is required.")
        return 

    domain_input = input("Enter the domain (optional, press Enter to skip): ").strip()
    domain = normalize_domain(domain_input) if domain_input else None

    pages, domain = fetch_pages(investor_name, domain)

    for page in pages:
        print(page.dimension, "->", page.final_url, ":", page.title)

    title_counts = count_titles(pages)
    pages_dimension = [p for p in pages if not is_empty_page(p, title_counts)]
    results = []
    for page in pages_dimension:
        result = call_extraction(client, investor_name, page)
        filtered = apply_post_filter(result, page)
        results.append(filtered)

    profile = build_investor_profile(investor_name, domain, pages, results)
    strategy = call_strategy(client, profile)
    brief = render_brief(profile, strategy)

    output_path = f"output/brief_{investor_name.replace(' ', '_')}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(brief)
    if config.DEBUG_MODE:
        print("=== PROFILE BUILD ===")
        print(profile)
        print("=== STRATEGY BUILD ===")
        print(strategy)
        print("=== BRIEF ===")
        print(brief)

if __name__ == "__main__":
    main()