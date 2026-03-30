import logging
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def verify_cpa_nasba(first_name, last_name, state, license_number):
    """
    Scrapes the NASBA CPA lookup tool to verify a CPA license.
    Returns: dict {'is_valid': bool, 'message': str}
    """
    logger.info(f"Starting auto-verification for {first_name} {last_name} | {state} - {license_number}")
    
    try:
        with sync_playwright() as p:
            # Launch headless chromium
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Go to the NASBA lookup page
            page.goto('https://ald.nasba.org/search/cpa')
            
            # Wait for form elements
            page.wait_for_selector('button#terms')
            
            # Click terms checkbox
            page.click('button#terms')
            
            # Input fields
            if first_name:
                page.fill('input#firstName', first_name)
            page.fill('input#lastName', last_name)
            page.fill('input#licenseNum', license_number)
            
            # Note: We omit state (jurisdictionId) to search all jurisdictions, handling differences in state name formats.
            
            # Click search
            page.click('button.bg-primary')
            
            # Wait for results or failure text
            try:
                # Wait up to 15 seconds for a result link. The site uses React so we wait for network/dom changes.
                # If no results are found, it should render "No results found." somewhere.
                # We'll wait a bit and check the page content text to cover both.
                page.wait_for_timeout(5000) # Give it 5s to search
            except Exception as e:
                pass
                
            content = page.content()
            browser.close()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            page_text = soup.get_text()
            
            if "No results found" in page_text:
                return {'is_valid': False, 'message': 'No results found on NASBA registry.'}
                
            # Find result rows by href
            result_links = soup.find_all('a', href=lambda href: href and href.startswith('/search/cpa/'))
            
            if not result_links:
                return {'is_valid': False, 'message': 'Could not parse results from NASBA.'}
                
            first_result_text = result_links[0].get_text().upper()
            
            if 'ACTIVE' in first_result_text or 'ISSUED' in first_result_text:
                return {'is_valid': True, 'message': 'License verified as active/issued on NASBA.'}
            elif 'EXPIRED' in first_result_text:
                return {'is_valid': False, 'message': 'License found, but is EXPIRED.'}
            elif 'REVOKED' in first_result_text:
                return {'is_valid': False, 'message': 'License found, but is REVOKED.'}
                
            return {'is_valid': True, 'message': 'License found (status ambiguous).'}
            
    except Exception as e:
        logger.error(f"Error scraping NASBA: {str(e)}")
        return {'is_valid': False, 'message': f'System error during verification: {str(e)}'}
