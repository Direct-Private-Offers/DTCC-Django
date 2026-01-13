import re

with open('config/settings. py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove ALL spaces after ANY dot (handles multiple spaces too)
content = re.sub(r'\.\s+', '.', content)

with open('config/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed ALL spaces after dots!")