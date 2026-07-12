import urllib.request
import json
import ssl

def check_finra(crd):
    url = f"https://api.brokercheck.finra.org/search/individual/{crd}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
            print(data)
    except Exception as e:
        print("Error:", e)

check_finra('6059104') # Example CRD, random
