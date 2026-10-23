import os
import re

directories = [
    'app/templates/doctor',
    'app/templates/admin',
    'app/templates/patient'
]

pattern = re.compile(r'{%\s*block\s+sidebar_profile\s*%}.*?{\s*%\s*endblock\s*%}', re.DOTALL)

for directory in directories:
    if not os.path.exists(directory): continue
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if pattern.search(content):
                new_content = pattern.sub('', content)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Removed sidebar_profile block from {filepath}")
