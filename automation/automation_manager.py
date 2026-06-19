# automate.py — Automation Manager for Ben AI
# Handles image downloads, video downloads, Amazon automation, and web scraping
# Uses Edge WebDriver for browser automation tasks

import threading
import queue
import time
import json
import subprocess
import os
import re
import requests
import ssl
import logging

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[Automate] Selenium not installed. Browser automation disabled.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutomationManager:
    def __init__(self, task_queue):
        self.task_queue = task_queue
        self.result_queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self.driver = None
        self.driver_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Edge WebDriver setup
    # ------------------------------------------------------------------
    def _get_driver(self):
        with self.driver_lock:
            if self.driver is not None:
                return self.driver
            if not SELENIUM_AVAILABLE:
                return None
            try:
                options = EdgeOptions()
                options.add_argument("--start-maximized")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-web-security")
                options.add_argument("--allow-running-insecure-content")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-plugins-discovery")

                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=options)
                self.driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                return self.driver
            except Exception as e:
                logger.error(f"Edge WebDriver setup failed: {e}")
                return None

    # ------------------------------------------------------------------
    # Worker thread
    # ------------------------------------------------------------------
    def _worker(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=0.5)
                result = self._execute_task(task)
                if result is not None:
                    self.result_queue.put(result)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
                self.result_queue.put(json.dumps({"error": str(e)}))

    def _execute_task(self, task):
        action = task.get("action", "")
        try:
            if action == "download_images":
                return self._download_images(task.get("query", ""), task.get("count", 5))
            elif action == "download_video":
                return self._download_video(task.get("url", ""), task.get("query", ""), task.get("count", 1))
            elif action == "amazon_search":
                return self._amazon_search(task.get("product", ""))
            elif action == "amazon_add_to_cart":
                return self._amazon_add_to_cart(task.get("asin", ""))
            elif action == "amazon_place_order":
                return self._amazon_place_order()
            elif action == "scrape":
                return self._scrape(task.get("url", ""), task.get("selector"))
            else:
                return json.dumps({"error": f"Unknown automation action: {action}"})
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return json.dumps({"error": str(e)})

    # ------------------------------------------------------------------
    # Download Images (requests-based, no browser needed)
    # ------------------------------------------------------------------
    def _download_images(self, query, count=5):
        """Download images using requests-based approach to avoid WebDriver issues."""
        try:
            os.makedirs("downloads/images", exist_ok=True)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            search_url = f"https://www.google.com/search?q={query}&tbm=isch"

            # Try using bing_image_downloader first
            try:
                from bing_image_downloader import downloader
                downloader.download(query, limit=count, output_dir="downloads/images",
                                    adult_filter_off=True, force_replace=False, timeout=30)
                return json.dumps({"downloaded": count, "query": query, "status": "completed"})
            except ImportError:
                pass

            # Fallback: scrape image URLs from Google
            response = requests.get(search_url, headers=headers, timeout=15, verify=False)
            if response.status_code != 200:
                return json.dumps({"error": f"Failed to fetch search results: {response.status_code}"})

            # Extract image URLs
            image_urls = re.findall(r'"(https?://[^"]*\.(?:jpg|jpeg|png))"', response.text)
            if not image_urls:
                image_urls = re.findall(r'"([^"]*\.jpe?g|[^"]*\.png)"', response.text)

            downloaded = 0
            for i, url in enumerate(image_urls[:count]):
                try:
                    if not url.startswith("http"):
                        continue
                    img_response = requests.get(url, headers=headers, timeout=10, verify=False)
                    if img_response.status_code == 200:
                        ext = ".jpg" if ".jpg" in url or ".jpeg" in url else ".png"
                        filename = f"downloads/images/{query.replace(' ', '_')}_{i}{ext}"
                        with open(filename, "wb") as f:
                            f.write(img_response.content)
                        downloaded += 1
                except Exception as e:
                    logger.warning(f"Failed to download image {i}: {e}")
                    continue

            return json.dumps({"downloaded": downloaded, "query": query, "status": "completed"})

        except Exception as e:
            logger.error(f"Image download failed: {e}")
            return json.dumps({"error": str(e)})

    # ------------------------------------------------------------------
    # Download Video (yt-dlp)
    # ------------------------------------------------------------------
    def _download_video(self, url="", query="", count=1):
        """Download video using yt-dlp."""
        try:
            os.makedirs("downloads/videos", exist_ok=True)
            if url:
                target = url
            elif query:
                target = f"ytsearch{count}:{query}"
            else:
                return json.dumps({"error": "No URL or query provided"})

            result = subprocess.run(
                ["yt-dlp", "-o", "downloads/videos/%(title)s.%(ext)s", target],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                return json.dumps({"status": "completed", "output": result.stdout[:500]})
            else:
                return json.dumps({"error": f"Download failed: {result.stderr[:500]}"})
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Download timed out"})
        except Exception as e:
            logger.error(f"Video download failed: {e}")
            return json.dumps({"error": str(e)})

    # ------------------------------------------------------------------
    # Amazon Search
    # ------------------------------------------------------------------
    def _amazon_search(self, product):
        """Search for products on Amazon."""
        driver = self._get_driver()
        if not driver:
            return json.dumps({"error": "Unable to initialize web driver"})
        try:
            driver.get("https://www.amazon.in")
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
            )
            search_box.clear()
            search_box.send_keys(product)
            search_box.submit()

            time.sleep(3)
            items = driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            results = []
            for item in items[:5]:
                try:
                    title = item.find_element(By.CSS_SELECTOR, "h2 a span").text
                    try:
                        price = item.find_element(By.CSS_SELECTOR, ".a-price-whole").text
                    except Exception:
                        price = "N/A"
                    link = item.find_element(By.CSS_SELECTOR, "h2 a").get_attribute("href")
                    results.append({"title": title, "price": price, "link": link})
                except Exception as e:
                    logger.warning(f"Error parsing item: {e}")
                    continue

            return json.dumps({"results": results})
        except Exception as e:
            logger.error(f"Amazon search failed: {e}")
            return json.dumps({"error": str(e)})

    # ------------------------------------------------------------------
    # Amazon Add to Cart
    # ------------------------------------------------------------------
    def _amazon_add_to_cart(self, asin):
        """Add product to cart on Amazon."""
        driver = self._get_driver()
        if not driver:
            return json.dumps({"error": "Unable to initialize web driver"})
        try:
            driver.get(f"https://www.amazon.in/dp/{asin}")
            add_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "add-to-cart-button"))
            )
            add_btn.click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "huc-v2-order-row-confirm-text"))
            )
            return json.dumps({"status": "added"})
        except Exception as e:
            logger.error(f"Add to cart failed: {e}")
            return json.dumps({"error": f"Could not add to cart: {e}"})

    # ------------------------------------------------------------------
    # Amazon Place Order (COD)
    # ------------------------------------------------------------------
    def _amazon_place_order(self):
        """Place an order on Amazon (requires login)."""
        driver = self._get_driver()
        if not driver:
            return json.dumps({"error": "Unable to initialize web driver"})
        try:
            driver.get("https://www.amazon.in/gp/cart/view.html")
            # Check if cart is empty
            empty = driver.find_elements(By.ID, "sc-empty-cart")
            if empty:
                return json.dumps({"error": "Cart is empty"})

            # Proceed to checkout
            checkout_btns = driver.find_elements(By.CSS_SELECTOR, "input[name='proceedToRetailCheckout']")
            if not checkout_btns:
                return json.dumps({"error": "No proceed to checkout button found"})
            checkout_btns[0].click()

            time.sleep(3)

            # Select address if needed
            addr_btns = driver.find_elements(By.CSS_SELECTOR, "input[value='SHIP_TO_THIS_ADDRESS']")
            if addr_btns:
                addr_btns[0].click()
                time.sleep(2)

            # Continue buttons
            cont_btns = driver.find_elements(By.CSS_SELECTOR, "input[value='Continue']")
            if cont_btns:
                cont_btns[0].click()
                time.sleep(2)

            # Select COD payment
            payment_methods = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][name='paymentMethod']")
            cod_selected = False
            for pm in payment_methods:
                if pm.get_attribute("value") == "P_COD":
                    pm.click()
                    cod_selected = True
                    break

            if not cod_selected and not payment_methods:
                return json.dumps({"error": "No payment methods available"})

            time.sleep(2)

            # Place order
            place_btns = driver.find_elements(By.CSS_SELECTOR, "input[name='placeYourOrder1']")
            if place_btns:
                place_btns[0].click()
                time.sleep(5)
                # Check for confirmation
                confirm = driver.find_elements(By.CSS_SELECTOR, ".a-color-price")
                order_panel = driver.find_elements(By.CSS_SELECTOR, "#orderConfirmationLeftPanel")
                if confirm or order_panel:
                    return json.dumps({"status": "order_placed"})

            return json.dumps({"error": "Order placement failed"})
        except Exception as e:
            logger.error(f"Could not place order: {e}")
            return json.dumps({"error": f"Could not place order: {e}"})

    # ------------------------------------------------------------------
    # Web Scraping
    # ------------------------------------------------------------------
    def _scrape(self, url, selector=None):
        """Scrape content from a webpage."""
        driver = self._get_driver()
        if not driver:
            return json.dumps({"error": "Unable to initialize web driver"})
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)

            if selector:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                texts = [el.text.strip() for el in elements if el.text.strip()]
                if texts:
                    return json.dumps({"data": texts, "count": len(texts), "status": "completed"})
                else:
                    return json.dumps({"data": [], "count": 0, "status": "no_matches"})
            else:
                body = driver.find_element(By.TAG_NAME, "body")
                text = body.text[:5000]  # Limit to 5000 chars
                return json.dumps({"data": text, "status": "completed"})

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return json.dumps({"error": str(e)})

    # ------------------------------------------------------------------
    # Result retrieval
    # ------------------------------------------------------------------
    def get_result(self, block=False, timeout=1):
        """Get result from result queue."""
        try:
            return self.result_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    def stop(self):
        """Stop the automation manager."""
        self.running = False
        with self.driver_lock:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
