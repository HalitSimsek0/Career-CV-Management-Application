import re

# Şirket listesini buraya yapıştırın
# Paste your company list here
text = '''
'''

# Kategori başlıklarını buraya yazın
# Add category headers here
headers = [
    ]

headers_lower = set(h.lower() for h in headers)
lines = text.split('\n')
companies = []
seen = set()

for line in lines:
    line = line.strip()
    if not line:
        continue
    if line.lower() in headers_lower:
        continue
    
    lower_line = line.lower().replace('ı', 'i').replace('i̇', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g').replace('ö', 'o').replace('ü', 'u')
    if lower_line not in seen:
        seen.add(lower_line)
        companies.append(line)

with open('deduplicated_companies.txt', 'w', encoding='utf-8') as f:
    for c in companies:
        f.write(c + '\n')
print(f'Total unique companies: {len(companies)}')
