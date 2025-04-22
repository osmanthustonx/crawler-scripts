#!/usr/bin/env python3
import sys
import json
import time
import os
import traceback
from typing import List, Dict, Any, Optional, Union

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Constants
BASE_URL = "https://gmgn.ai/sol/address/{}"
DEFAULT_TIMEOUT = 10
PAGE_LOAD_WAIT = 3
ANIMATION_WAIT = 2

def log(message: str, debug: bool = False) -> None:
    """Print debug messages to stderr if debug mode is enabled.
    
    Args:
        message: The message to log
        debug: Whether to print the message
    """
    if debug:
        print(message, file=sys.stderr)

def setup_driver(keep_browser_open: bool = False) -> uc.Chrome:
    """Configure and initialize the Chrome WebDriver.
    
    Args:
        keep_browser_open: Whether to keep the browser open after completion
        
    Returns:
        An instance of undetected_chromedriver Chrome
    """
    # Configure Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Handle display environment variable if present
    display = os.environ.get("DISPLAY", None)
    if display:
        options.add_argument(f"--display={display}")
    
    # Enable performance logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Create driver
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(60)
    
    return driver

def click_element_by_js(driver: uc.Chrome, element, debug: bool = False) -> bool:
    """Click an element using JavaScript to avoid potential WebDriver issues.
    
    Args:
        driver: The WebDriver instance
        element: The WebElement to click
        debug: Whether to log debug messages
        
    Returns:
        True if successful, False otherwise
    """
    try:
        driver.execute_script("arguments[0].click();", element)
        log(f"Clicked element using JavaScript: {element.get_attribute('outerHTML')}", debug)
        return True
    except Exception as e:
        log(f"Error clicking element: {e}", debug)
        return False

def find_and_click_element(driver: uc.Chrome, by: By, selector: str, 
                          description: str, debug: bool = False) -> bool:
    """Find an element by selector and click it.
    
    Args:
        driver: The WebDriver instance
        by: The method to locate elements
        selector: The selector string
        description: Description of the element for logging
        debug: Whether to log debug messages
        
    Returns:
        True if successful, False otherwise
    """
    log(f"Looking for '{description}' element...", debug)
    try:
        element = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located((by, selector))
        )
        log(f"Found '{description}' element", debug)
        return click_element_by_js(driver, element, debug)
    except Exception as e:
        log(f"Error finding or clicking '{description}' element: {e}", debug)
        return False

def complete_onboarding_flow(driver: uc.Chrome, debug: bool = False) -> bool:
    """Complete the onboarding flow by clicking through intro screens.
    
    Args:
        driver: The WebDriver instance
        debug: Whether to log debug messages
        
    Returns:
        True if successful, False otherwise
    """
    # Try to close intro modal if present
    try:
        close_icons = driver.find_elements(By.CLASS_NAME, "css-pt4g3d")
        if close_icons:
            click_element_by_js(driver, close_icons[0], debug)
    except Exception as e:
        log(f"Error closing intro modal: {e}", debug)
    
    # Click through the Next buttons
    try:
        for _ in range(3):
            next_button = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[contains(@class, 'pi-btn')]//span[text()='Next']/..")
                )
            )
            click_element_by_js(driver, next_button, debug)
            time.sleep(ANIMATION_WAIT)
        
        # Click Finish button
        finish_selector = "//button[contains(@class, 'pi-btn')]//span[text()='Finish']/.."
        find_and_click_element(driver, By.XPATH, finish_selector, "Finish button", debug)
        time.sleep(ANIMATION_WAIT)
        
        return True
    except Exception as e:
        log(f"Error in onboarding flow: {e}", debug)
        return False

def navigate_to_wallet_page(driver: uc.Chrome, wallet_address: str, debug: bool = False) -> bool:
    """Navigate to the wallet page and prepare it for data extraction.
    
    Args:
        driver: The WebDriver instance
        wallet_address: The wallet address to analyze
        debug: Whether to log debug messages
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Enable network monitoring
        log("Setting up network interception...", debug)
        driver.execute_cdp_cmd('Network.enable', {})
        
        # Clear existing logs
        driver.get_log('performance')
        
        # Navigate to the URL
        wallet_url = BASE_URL.format(wallet_address)
        log(f"Navigating to {wallet_url}...", debug)
        driver.get(wallet_url)
        
        # Wait for the page to load
        log("Waiting for page to load...", debug)
        time.sleep(PAGE_LOAD_WAIT)
        
        # Complete onboarding flow
        if not complete_onboarding_flow(driver, debug):
            log("Warning: Onboarding flow may not have completed successfully", debug)
        
        # Click on Recent PnL tab
        find_and_click_element(
            driver, By.XPATH, "//*[contains(text(), 'Recent PnL')]", 
            "Recent PnL", debug
        )
        
        # Scroll the page to load all content
        scroll_page_for_content(driver, debug)
        
        return True
    except Exception as e:
        log(f"Error navigating to wallet page: {e}", debug)
        return False

def scroll_page_for_content(driver: uc.Chrome, debug: bool = False) -> None:
    """Scroll all scrollable containers to load content.
    
    Args:
        driver: The WebDriver instance
        debug: Whether to log debug messages
    """
    log("Scrolling to load all content...", debug)
    
    # JavaScript to find all scrollable containers and scroll them
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
    
    # Execute scroll script and log results
    scroll_result = driver.execute_script(js_find_and_scroll)
    log(f"Found {scroll_result['totalContainers']} scrollable containers and "
        f"scrolled {scroll_result['scrolledContainers']}", debug)
    
    # Wait for content to load
    time.sleep(ANIMATION_WAIT)
    
    # Scroll again to catch any newly loaded content
    driver.execute_script(js_find_and_scroll)
    log("Performed second scroll to catch dynamically loaded content", debug)
    time.sleep(ANIMATION_WAIT)

def extract_network_data(driver: uc.Chrome, debug: bool = False) -> Dict[str, Any]:
    """Extract wallet data from network requests.
    
    Args:
        driver: The WebDriver instance
        debug: Whether to log debug messages
        
    Returns:
        Dictionary containing wallet summary and holdings data
    """
    logs = driver.get_log('performance')
    wallet_summary_data = None
    wallet_holdings_data = []
    
    for entry in logs:
        try:
            if 'message' not in entry:
                continue
                
            message = json.loads(entry['message'])
            if ('message' not in message or 
                'method' not in message['message'] or 
                message['message']['method'] != 'Network.responseReceived'):
                continue
                
            params = message['message']['params']
            request_id = params['requestId']
            url = params['response']['url']
            
            # Extract wallet summary data
            if '/api/v1/wallet_stat/sol/' in url:
                log(f"Found wallet summary request: {url}", debug)
                try:
                    response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                    if 'body' in response:
                        wallet_summary_data = json.loads(response['body'])['data']
                        log("Successfully captured wallet summary data", debug)
                except Exception as e:
                    log(f"Error extracting wallet summary data: {e}", debug)
            
            # Extract wallet holdings data
            elif '/api/v1/wallet_holdings' in url:
                log(f"Found wallet holdings request: {url}", debug)
                try:
                    response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                    if 'body' in response:
                        wallet_holdings = json.loads(response['body'])
                        wallet_holdings_data.extend(wallet_holdings['data']['holdings'])
                        log("Successfully captured wallet holdings data", debug)
                except Exception as e:
                    log(f"Error extracting wallet holdings data: {e}", debug)
        except Exception as e:
            log(f"Error processing network log entry: {e}", debug)
    
    return {
        "wallet_summary": wallet_summary_data,
        "wallet_holdings": wallet_holdings_data
    }

def analyze_wallet(wallet_address: str, driver: uc.Chrome, debug: bool = False) -> Dict[str, Any]:
    """Analyze a single wallet address.
    
    Args:
        wallet_address: The wallet address to analyze
        driver: The WebDriver instance
        debug: Whether to log debug messages
        
    Returns:
        Dictionary containing analysis results or error
    """
    log(f"Processing wallet: {wallet_address}", debug)
    
    try:
        if navigate_to_wallet_page(driver, wallet_address, debug):
            return extract_network_data(driver, debug)
        else:
            return {"error": "Failed to navigate to wallet page"}
    except Exception as e:
        log(f"Error analyzing wallet {wallet_address}: {e}", debug)
        return {"error": str(e)}

def wallet_analysis(
    wallet_addresses: Union[str, List[str]], 
    keep_browser_open: bool = False, 
    clean_output: bool = False
) -> Dict[str, Any]:
    """Analyze multiple wallet addresses and extract their data.
    
    Args:
        wallet_addresses: Single wallet address or list of addresses
        keep_browser_open: Whether to keep the browser open after completion
        clean_output: Whether to produce clean output (no formatting or debug info)
        
    Returns:
        Dictionary mapping wallet addresses to their analysis results
    """
    # Normalize input to list
    if isinstance(wallet_addresses, str):
        wallet_addresses = [wallet_addresses]
    
    log(f"Starting wallet analysis for {len(wallet_addresses)} wallets...", not clean_output)
    all_results = {}
    driver = None
    
    try:
        driver = setup_driver(keep_browser_open)
        
        # Process each wallet address
        for wallet_address in wallet_addresses:
            all_results[wallet_address] = analyze_wallet(wallet_address, driver, not clean_output)
        
        # Handle keep_browser_open flag
        if keep_browser_open:
            print(json.dumps(all_results, indent=2))
            log("Debug session complete. Browser will remain open for inspection.", not clean_output)
            log("Press Ctrl+C to close the browser and exit.", not clean_output)
            
            # Keep the script running
            while True:
                time.sleep(3)
        elif driver:
            log("Debug session complete. Closing browser.", not clean_output)
            driver.quit()
            
    except Exception as e:
        log(f"Error in wallet analysis: {e}", not clean_output)
        log(traceback.format_exc(), not clean_output)
        
        # Keep the browser open for inspection if requested
        if keep_browser_open and driver:
            log("Browser will remain open for inspection due to error.", not clean_output)
            while True:
                time.sleep(3)
        elif driver:
            driver.quit()
    
    # Output the results
    if clean_output:
        print(json.dumps(all_results))
    else:
        print(json.dumps(all_results, indent=2))
    
    return all_results

def parse_arguments() -> tuple:
    """Parse command line arguments.
    
    Returns:
        Tuple of (wallet_addresses, keep_browser_open, clean_output)
    """
    if len(sys.argv) < 2:
        print("Usage: python3 wallet_analysis.py <wallet_address1> [wallet_address2 ...] [keep_open] [clean]")
        print("  <wallet_address1> [wallet_address2 ...] - One or more wallet addresses to analyze")
        print("  [keep_open] - Optional: 'keep_open' to keep the browser open after completion")
        print("  [clean] - Optional: 'clean' to output only the JSON data")
        sys.exit(1)
    
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
        
    return wallet_addresses, keep_browser_open, clean_output

if __name__ == "__main__":
    wallet_addresses, keep_browser_open, clean_output = parse_arguments()
    wallet_analysis(wallet_addresses, keep_browser_open, clean_output) 