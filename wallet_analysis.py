#!/usr/bin/env python3
import sys
import json
import time
import os
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

def log(message, debug=False):
    """Print debug messages to stderr if debug mode is enabled"""
    if debug:
        print(message, file=sys.stderr)

def wallet_analysis(wallet_addresses, keep_browser_open=False, clean_output=False):
    """Debug wallet analysis using undetected-chromedriver"""
    if isinstance(wallet_addresses, str):
        wallet_addresses = [wallet_addresses]
    
    log(f"Starting wallet analysis for {len(wallet_addresses)} wallets...", not clean_output)
    
    try:
        # Configure Chrome options
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        display = os.environ.get("DISPLAY", None)
        if display:
            options.add_argument(f"--display={display}")
        
        # Enable performance logging
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # Create a new instance of the undetected Chrome driver
        driver = uc.Chrome(options=options)
        
        # Set page load timeout
        driver.set_page_load_timeout(60)
        
        # Process each wallet address
        all_results = {}
        
        for wallet_address in wallet_addresses:
            log(f"Processing wallet: {wallet_address}", not clean_output)
            
            try:
                # Enable network monitoring BEFORE navigating to the page
                log("Setting up network interception...", not clean_output)
                driver.execute_cdp_cmd('Network.enable', {})
                
                # Clear existing logs
                driver.get_log('performance')
                
                # Navigate to the URL
                wallet_url = f"https://gmgn.ai/sol/address/{wallet_address}"
                log(f"Navigating to {wallet_url}...", not clean_output)
                driver.get(wallet_url)
                
                # Wait for the page to load
                log("Waiting for page to load...", not clean_output)
                time.sleep(3)  # Increased wait time
                
                # Find and click the close icon if it exists
                log("Looking for close icon...", not clean_output)
                try:
                    close_icons = driver.find_elements(By.CLASS_NAME, "css-pt4g3d")
                    if len(close_icons) >= 1:
                        close_icon = close_icons[0]
                        log(f"Found close icon", not clean_output)
                        
                        # Use JavaScript to click the element
                        driver.execute_script("arguments[0].click();", close_icon)
                        log("Clicked close icon using JavaScript", not clean_output)
                    else:
                        log(f"Not enough close icons found. Found {len(close_icons)} elements with class css-pt4g3d", not clean_output)
                except Exception as e:
                    log(f"Error clicking close icon: {e}", not clean_output)

                for j in range(3):
                    # Wait for the Next button to be present
                    next_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'pi-btn')]//span[text()='Next']/.."))
                    )
                    log(f"Found Next button: {next_button.get_attribute('outerHTML')}", not clean_output)
                    
                    # Use JavaScript to click the element
                    driver.execute_script("arguments[0].click();", next_button)
                    log("Clicked Next button using JavaScript", not clean_output)
                    
                    # Wait a moment for any animations or page changes
                    time.sleep(2)
                
                # Step 1.6: Find and click the Finish button
                log("Looking for Finish button...", not clean_output)
                try:
                    # Wait for the Finish button to be present
                    finish_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'pi-btn')]//span[text()='Finish']/.."))
                    )
                    log(f"Found Finish button: {finish_button.get_attribute('outerHTML')}", not clean_output)
                    
                    # Use JavaScript to click the element
                    driver.execute_script("arguments[0].click();", finish_button)
                    log("Clicked Finish button using JavaScript", not clean_output)
                    
                    # Wait a moment for any animations or page changes
                    time.sleep(2)
                except Exception as e:
                    log(f"Error clicking Finish button: {e}", not clean_output)
                
                # Find and click the "Recent PnL" element
                log("Looking for 'Recent PnL' element...", not clean_output)
                try:
                    # Try to find the element by text
                    recent_pnl_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Recent PnL')]")
                    if len(recent_pnl_elements) >= 1:
                        recent_pnl = recent_pnl_elements[0]
                        log(f"Found 'Recent PnL' element", not clean_output)
                        
                        # Use JavaScript to click the element
                        driver.execute_script("arguments[0].click();", recent_pnl)
                        log("Clicked 'Recent PnL' element using JavaScript", not clean_output)
                    else:
                        log(f"'Recent PnL' element not found", not clean_output)
                except Exception as e:
                    log(f"Error clicking 'Recent PnL' element: {e}", not clean_output)
                
                # Try multiple scrolling methods to ensure the page scrolls properly
                log("Scrolling to bottom of page...", not clean_output)
                # Find all scrollable containers and scroll each one to the bottom
                js_find_and_scroll = """
                let containers = Array.from(document.querySelectorAll('*')).filter(el => {
                  let style = window.getComputedStyle(el);
                  return (style.overflowY === 'scroll' || style.overflowY === 'auto') &&
                         el.scrollHeight > el.clientHeight;
                });
                
                let scrolledContainers = 0;
                containers.forEach(container => {
                  container.scrollTop = container.scrollHeight;
                  scrolledContainers++;
                });
                
                return {
                  totalContainers: containers.length,
                  scrolledContainers: scrolledContainers
                };
                """
                
                # Execute the script and get the result
                scroll_result = driver.execute_script(js_find_and_scroll)
                log(f"Found {scroll_result['totalContainers']} scrollable containers and scrolled {scroll_result['scrolledContainers']}", not clean_output)
                
                # Wait a moment to let any lazy-loaded content appear
                time.sleep(2)
                
                # Scroll one more time to get any newly loaded content
                driver.execute_script(js_find_and_scroll)
                log("Performed second scroll to catch any dynamically loaded content", not clean_output)
                
                # Get all network requests
                logs = driver.get_log('performance')
                wallet_summary_data = None
                wallet_holdings_data = []
                
                # Process all network requests in a single loop
                for entry in logs:
                    if 'message' in entry:
                        message = json.loads(entry['message'])
                        if 'message' in message and 'method' in message['message']:
                            if message['message']['method'] == 'Network.responseReceived':
                                params = message['message']['params']
                                request_id = params['requestId']
                                url = params['response']['url']
                                
                                # Look for the wallet summary API
                                if '/api/v1/wallet_stat/sol/' in url:
                                    log(f"Found wallet summary request: {url}", not clean_output)
                                    try:
                                        # Get response body
                                        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                        if 'body' in response:
                                            wallet_summary_data = json.loads(response['body'])['data']
                                            log("Successfully captured wallet summary data", not clean_output)
                                    except Exception as e:
                                        log(f"Error getting wallet summary response body: {e}", not clean_output)
                                
                                # Look for the wallet holdings API
                                elif '/api/v1/wallet_holdings' in url:
                                    log(f"Found wallet holdings request: {url}", not clean_output)
                                    try:
                                        # Get response body
                                        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                        if 'body' in response:
                                            wallet_holdings = json.loads(response['body'])
                                            wallet_holdings_data.extend(wallet_holdings['data']['holdings'])
                                            log("Successfully captured wallet holdings data", not clean_output)
                                    except Exception as e:
                                        log(f"Error getting wallet holdings response body: {e}", not clean_output)
                # Store the results for this wallet
                all_results[wallet_address] = {
                    "wallet_summary": wallet_summary_data,
                    "wallet_holdings": wallet_holdings_data
                }
                
            except Exception as e:
                log(f"Error processing wallet {wallet_address}: {e}", not clean_output)
                all_results[wallet_address] = {
                    "error": str(e)
                }
        
        # Keep the browser open for inspection if requested
        if keep_browser_open:
            print(json.dumps(all_results, indent=2))
            log("Debug session complete. Browser will remain open for inspection.", not clean_output)
            log("Press Ctrl+C to close the browser and exit.", not clean_output)
            
            # Keep the script running
            while True:
                time.sleep(3)
        else:
            log("Debug session complete. Closing browser.", not clean_output)
            driver.quit()
            
    except Exception as e:
        log(f"Error in debug wallet analysis script: {e}", not clean_output)
        log(traceback.format_exc(), not clean_output)
        
        # Keep the browser open for inspection in case of error if requested
        if keep_browser_open:
            log("Browser will remain open for inspection due to error.", not clean_output)
            # Keep the browser open for inspection in case of error
            while True:
                time.sleep(3)
        else:
            driver.quit()
    
    # Output the results
    if clean_output:
        print(json.dumps(all_results))
    else:
        print(json.dumps(all_results, indent=2))
    
    return all_results

if __name__ == "__main__":
    # Get wallet addresses from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 wallet_analysis.py <wallet_address1> [wallet_address2 ...] [keep_open] [clean]")
        print("  <wallet_address1> [wallet_address2 ...] - One or more wallet addresses to analyze")
        print("  [keep_open] - Optional: 'keep_open' to keep the browser open after completion")
        print("  [clean] - Optional: 'clean' to output only the JSON data")
        sys.exit(1)
    
    # Parse command line arguments
    wallet_addresses = []
    keep_browser_open = False
    clean_output = False
    
    for arg in sys.argv[1:]:
        if arg.lower() == 'keep_open':
            keep_browser_open = True
        elif arg.lower() == 'clean':
            clean_output = True
        else:
            wallet_addresses.append(arg)
    
    if not wallet_addresses:
        print("Error: No wallet addresses provided")
        sys.exit(1)
    
    wallet_analysis(wallet_addresses, keep_browser_open, clean_output) 