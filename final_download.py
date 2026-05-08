import urllib.request
import os

os.makedirs('data/images', exist_ok=True)

images = {
    "Norvasc_5mg.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Amlodipine_5mg_Tablets.jpg/800px-Amlodipine_5mg_Tablets.jpg",
    "Diabex_500mg.jpg": "https://upload.wikimedia.org/wikipedia/commons/5/51/Metformin_500mg_Tablets.jpg",
    "Plavix_75mg.jpg": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Clopidogrel_75mg_tablets.jpg",
    "Tylenol_500mg.jpg": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Tylenol_500_mg_capsules.jpg"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for name, url in images.items():
    print(f"Downloading {name}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(f"data/images/{name}", 'wb') as out_file:
                out_file.write(response.read())
        print(f"Successfully downloaded {name}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
