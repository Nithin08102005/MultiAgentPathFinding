import pymupdf

doc = pymupdf.open('c:/Users/raoni/OneDrive/Desktop/GitHub - Copy/The book of Abstracts final.pdf')
page = doc[8] # page 9
for block in page.get_text('dict')['blocks']:
    if block.get('type') == 0:
        for line in block['lines']:
            for span in line['spans']:
                text = span['text'].strip()
                if text:
                    font = span['font']
                    size = span['size']
                    color = hex(span['color'])
                    bbox = [round(x, 1) for x in span['bbox']]
                    print(f'{text[:45]:<45} | {font:<20} | {size:>4.1f}pt | {color:<8} | {bbox}')
