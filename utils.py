import re
import unicodedata

def clean_filename(filename: str) -> str:
    # Remove Unicode control characters and normalize
    clean = unicodedata.normalize('NFKD', filename)
    # Remove non-ASCII characters
    clean = clean.encode('ASCII', 'ignore').decode()
    # Replace spaces and unwanted characters
    clean = re.sub(r'[^\w\-\.]', '_', clean)
    return clean