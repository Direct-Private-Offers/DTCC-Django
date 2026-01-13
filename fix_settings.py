import re

with open('config/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix template context processors
content = re.sub(
    r"'django\.contrib\.auth\.context_processors\.auth',",
    "# 'django.contrib.auth.context_processors.auth',",
    content
)
content = re.sub(
    r"'django\.contrib\.messages\.context_processors\.messages',",
    "# 'django. contrib.messages.context_processors. messages',",
    content
)

# Replace AUTH_PASSWORD_VALIDATORS with empty list
content = re.sub(
    r"AUTH_PASSWORD_VALIDATORS = \[[^\]]+\]",
    "AUTH_PASSWORD_VALIDATORS = []",
    content,
    flags=re.DOTALL
)

with open('config/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Template processors and validators fixed!")