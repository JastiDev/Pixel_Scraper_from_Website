import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from playwright.async_api import async_playwright
import asyncio
import csv



# Function to run the script and handle UI updates
async def run_scraper(urls, results):
    for url in urls:
        print(url)
        results['per_url'][url] = []
        await check_pixels(url, results)
        await asyncio.sleep(2)


# Main scraping function
async def check_pixels(url, results):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        )

        pixels = {
            'dcm': set(),
            'ttd': set(),
            'facebook': set(),
            'linkedin': set()
        }
        all_requests = set()

        def handle_request(request):
            url_lower = request.url.lower()
            all_requests.add(request.url)
            print(url_lower)
            if 'https://ad.doubleclick.net/activity;register_conversion=1' in url_lower:
                pixels['dcm'].add(request.url)
                results['total_pixels']['dcm'].add(request.url)
            if 'adsrvr.org' in url_lower:
                pixels['ttd'].add(request.url)
                results['total_pixels']['ttd'].add(request.url)
            if 'https://www.facebook.com/tr/' in url_lower:
                pixels['facebook'].add(request.url)
                results['total_pixels']['facebook'].add(request.url)
            if 'https://px.ads.linkedin.com/' in url_lower:
                pixels['linkedin'].add(request.url)
                results['total_pixels']['linkedin'].add(request.url)

        page.on('request', handle_request)

        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=500000)
            await page.wait_for_timeout(5000)

            # Generalizing to all elements
            all_elements = await page.query_selector_all('*')  # All elements

            for elem in all_elements:
                # Check for href, src, onclick, and other attributes
                attributes = ['href', 'src', 'onclick']
                for attr in attributes:
                    link = await elem.get_attribute(attr)
                    if link and (
                        'https://ad.doubleclick.net/activity;register_conversion=1' in link or
                        'adsrvr.org' in link or
                        "https://www.facebook.com/tr/" in link or
                        "https://px.ads.linkedin.com/" in link
                    ):
                        action_type = 'link' if attr == 'href' else 'img' if attr == 'src' else 'onclick'
                        results['per_url'][url].append({
                            'action': action_type,
                            'element': link,
                            'dcm_count': len(pixels['dcm']),
                            'ttd_count': len(pixels['ttd']),
                            'facebook_count': len(pixels['facebook']),
                            'linkedin_count': len(pixels['linkedin']),
                            'dcm_pixels': list(pixels['dcm']),
                            'ttd_pixels': list(pixels['ttd']),
                            'facebook_pixels': list(pixels['facebook']),
                            'linkedin_pixels': list(pixels['linkedin'])
                        })

            # Scroll to the bottom to trigger additional pixel tracking (if needed)
            await page.evaluate("""window.scrollTo(0, document.body.scrollHeight);""")
            await page.wait_for_timeout(100000)

        except Exception as e:
            print(f"Error: {e}")
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



# Function to save results to CSV
def save_results_to_csv(results):
    with open('pixel_results_jake.csv', 'w', newline='') as f:
        writer = csv.writer(f)

        # Section 1: Per-URL results
        writer.writerow(["Per-URL Pixel Counts and URLs"])
        writer.writerow([
            "URL", "Action", "Element",
            "DCM Count", "DCM Pixels", 
            "TTD Count", "TTD Pixels",
            "Facebook Count", "Facebook Pixels",
            "LinkedIn Count", "LinkedIn Pixels"
        ])
        for url, actions in results['per_url'].items():
            for action in actions:
                writer.writerow([
                    url,
                    action['action'],
                    action['element'],
                    action['dcm_count'], "; ".join(action['dcm_pixels']),
                    action['ttd_count'], "; ".join(action['ttd_pixels']),
                    action['facebook_count'], "; ".join(action['facebook_pixels']),
                    action['linkedin_count'], "; ".join(action['linkedin_pixels'])
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

    print("Results saved to 'pixel_results_jake.csv'.")


# Function to handle button click in the UI
def start_scraper():
    urls = entry_urls.get("1.0", tk.END).strip().splitlines()
    if not urls:
        messagebox.showerror("Input Error", "Please enter at least one URL.")
        return

    results = {
        'per_url': {},
        'total_pixels': {
            'dcm': set(),
            'ttd': set(),
            'facebook': set(),
            'linkedin': set()
        }
    }

    # Run the scraper and update the UI
    asyncio.run(run_scraper(urls, results))

    # Save results to CSV
    save_results_to_csv(results)

    messagebox.showinfo("Scraper Finished", "Pixel tracking completed and results saved to CSV.")


# Set up the UI
root = tk.Tk()
root.title("Pixel Tracking Scraper")

# UI Layout
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

label_urls = ttk.Label(frame, text="Enter URLs (one per line):")
label_urls.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

# Use tk.Text instead of ttk.Text
entry_urls = tk.Text(frame, height=10, width=40)
entry_urls.grid(row=1, column=0, padx=5, pady=5)

btn_start = ttk.Button(frame, text="Start Scraper", command=start_scraper)
btn_start.grid(row=2, column=0, padx=5, pady=5)

root.mainloop()
