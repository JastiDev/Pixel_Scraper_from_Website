from playwright.async_api import async_playwright
import asyncio
import csv

async def check_pixels(url, results):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        )
        
        # Dictionaries to store pixels for each platform
        pixels = {
            'dcm': set(),
            'ttd': set(),
            'facebook': set(),
            'linkedin': set()
        }
        all_requests = set()  # For debugging

        def handle_request(request):
            url_lower = request.url.lower()
            all_requests.add(request.url)  # Log all requests

            # DCM Conversion Tracking
            if 'https://ad.doubleclick.net/activity;register_conversion=1' in url_lower:
                pixels['dcm'].add(request.url)
                results['total_pixels']['dcm'].add(request.url)

            # TTD Conversion Tracking
            if 'https://insight.adsrvr.org/track/' in url_lower:
                pixels['ttd'].add(request.url)
                results['total_pixels']['ttd'].add(request.url)

            # Any Facebook Tags (not just conversions)
            if 'https://www.facebook.com/tr/' in url_lower:
                pixels['facebook'].add(request.url)
                results['total_pixels']['facebook'].add(request.url)

            # Any LinkedIn Tags (not just conversions)
            if 'https://px.ads.linkedin.com/' in url_lower:
                pixels['linkedin'].add(request.url)
                results['total_pixels']['linkedin'].add(request.url)

        page.on('request', handle_request)

        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)  # Wait for ad scripts
            # print(f"Checked: {url}")
            # print(f"All requests for {url}: {len(all_requests)}")
            results['per_url'][url] = {
                'dcm_count': len(pixels['dcm']),
                'ttd_count': len(pixels['ttd']),
                'facebook_count': len(pixels['facebook']),
                'linkedin_count': len(pixels['linkedin']),
                'dcm_pixels': list(pixels['dcm']),
                'ttd_pixels': list(pixels['ttd']),
                'facebook_pixels': list(pixels['facebook']),
                'linkedin_pixels': list(pixels['linkedin'])
            }
        except Exception as e:
            # print(f"Error checking {url}: {e}")
            results['per_url'][url] = {
                'dcm_count': 0,
                'ttd_count': 0,
                'facebook_count': 0,
                'linkedin_count': 0,
                'dcm_pixels': [],
                'ttd_pixels': [],
                'facebook_pixels': [],
                'linkedin_pixels': []
            }
        finally:
            await browser.close()
            if not any(pixels.values()):
                print(f"No pixels found for {url}. All requests: {all_requests}")

urls = [
    "https://www.dell.com/en-us",
    # "https://www.dell.com/en-us/lp/simplifiedtech",
    # "https://www.dell.com/en-us/dt/welcome-to-now/smart-infrastructure.htm",
    # "https://www.dell.com/en-us/shop/scc/sc/storage-products",
    # "https://www.dell.com/en-us/shop/powerstore/sf/power-store"
]

results = {
    'per_url': {},
    'total_pixels': {
        'dcm': set(),
        'ttd': set(),
        'facebook': set(),
        'linkedin': set()
    }
}

async def main():
    for url in urls:
        await check_pixels(url, results)
        await asyncio.sleep(2)

# Run the script
asyncio.run(main())

# Save results to CSV
with open('pixel_results_jake.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    
    # Section 1: Per-URL results
    writer.writerow(["Per-URL Pixel Counts and URLs"])
    writer.writerow([
        "URL", 
        "DCM Count", "DCM Pixels", 
        "TTD Count", "TTD Pixels",
        "Facebook Count", "Facebook Pixels",
        "LinkedIn Count", "LinkedIn Pixels"
    ])
    for url, data in results['per_url'].items():
        writer.writerow([
            url,
            data['dcm_count'], "; ".join(data['dcm_pixels']),
            data['ttd_count'], "; ".join(data['ttd_pixels']),
            data['facebook_count'], "; ".join(data['facebook_pixels']),
            data['linkedin_count'], "; ".join(data['linkedin_pixels'])
        ])
    
    # Blank row for separation
    writer.writerow([])
    
    # Section 2: Total unique pixels
    writer.writerow(["Total Unique Pixel Counts and URLs"])
    writer.writerow(["Type", "Count", "Pixel URLs"])
    for platform, pixel_set in results['total_pixels'].items():
        writer.writerow([
            platform.upper(),
            len(pixel_set),
            "; ".join(sorted(pixel_set))
        ])

# Display summary in console
# print("Results saved to 'pixel_results_jake.csv'.")
# print("Summary:")
# for url, data in results['per_url'].items():
#     print(f"{url}:")
#     print(f"  DCM Conversions={data['dcm_count']}")
#     print(f"  TTD Conversions={data['ttd_count']}")
#     print(f"  Facebook Tags={data['facebook_count']}")
#     print(f"  LinkedIn Tags={data['linkedin_count']}")
# print("Total Unique Pixels:")
# for platform, pixel_set in results['total_pixels'].items():
#     print(f"  {platform.upper()}: {len(pixel_set)}")