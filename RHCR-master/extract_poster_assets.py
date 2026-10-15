import os
import pymupdf

os.makedirs('poster_assets', exist_ok=True)
doc = pymupdf.open('c:/Users/raoni/OneDrive/Desktop/GitHub - Copy/The book of Abstracts final.pdf')

assets = {
    'bg': 4752,
    'white_frame': 2974,
    'pill_green_1': 2971,
    'pill_blue_2': 2972,
    'pill_yellow_3': 2973,
    'badge_1': 2978,
    'badge_2': 2976,
    'badge_3': 2977,
    'divider': 2984,
    'pill_orange_4': 2979,
    'pill_purple_5': 2980,
    'badge_4': 2981,
    'badge_5': 2982,
    'keywords_bar': 3001,
}

for name, xref in assets.items():
    info = doc.extract_image(xref)
    pix = pymupdf.Pixmap(doc, xref)
    smask_xref = info.get('smask')
    if smask_xref:
        mask = pymupdf.Pixmap(doc, smask_xref)
        pix = pymupdf.Pixmap(pix, mask)
        ext = 'png'
    else:
        ext = info['ext']
    
    filename = os.path.join('poster_assets', f'{name}.{ext}')
    pix.save(filename)
    print(f'Saved {name} -> {filename} (alpha: {pix.alpha})')

print("All assets successfully extracted with alpha masks!")
