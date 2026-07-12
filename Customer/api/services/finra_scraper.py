import logging
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def verify_financial_pro_finra(crd_number, firm_crd, zip_code):
    """
    Scrapes FINRA BrokerCheck to verify a Financial Professional.
    Returns: dict {'is_valid': bool, 'message': str}
    """
    logger.info(f"Starting FINRA auto-verification for CRD: {crd_number} | Firm: {firm_crd} | ZIP: {zip_code}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # BrokerCheck often uses a direct URL pattern for individuals:
            url = f'https://brokercheck.finra.org/individual/summary/{crd_number}'
            page.goto(url)
            
            # Wait for either the summary page to load or a "no results" page
            try:
                page.wait_for_timeout(5000) # Give the SPA time to load
            except Exception:
                pass
                
            content = page.content()
            browser.close()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            page_text = soup.get_text()
            
            if "Page Not Found" in page_text or "No Results Found" in page_text:
                return {'is_valid': False, 'message': 'No results found on FINRA BrokerCheck.'}
                
            # Basic validation
            # Look for indicators of active registration.
            if "Currently registered" in page_text or "Broker" in page_text or "Investment Adviser" in page_text:
                return {'is_valid': True, 'message': 'Verified on FINRA BrokerCheck.'}
                
            if crd_number in page_text:
                return {'is_valid': True, 'message': 'Individual found on FINRA, please verify firm manually.'}
                
            return {'is_valid': False, 'message': 'Could not verify status unambiguously on FINRA.'}
            
    except Exception as e:
        logger.error(f"Error scraping FINRA: {str(e)}")
        return {'is_valid': False, 'message': f'System error during verification: {str(e)}'}
