import re
import glob

for filename in glob.glob('app/modules/*.py'):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace 'async def ' with 'def '
    new_content = re.sub(r'\basync\s+def\s+', 'def ', content)
    
    if content != new_content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filename}")

