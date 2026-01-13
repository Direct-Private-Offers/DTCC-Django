with open('config/settings.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('config/settings.py', 'w', encoding='utf-8') as f:
    for line in lines:
        # Comment out apps.core in INSTALLED_APPS
        if line.strip() == "'apps.core',":
            f.write("    # 'apps.core',\n")
        # Comment out RequestIDMiddleware
        elif "'apps. core.middleware.RequestIDMiddleware'" in line and not line.strip().startswith('#'):
            f.write("    # 'apps.core.middleware. RequestIDMiddleware',\n")
        else:
            f. write(line)

print("✅ apps.core removed!")

