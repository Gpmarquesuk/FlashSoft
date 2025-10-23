from pathlib import Path
text = Path('run.py').read_text()
print(text.find('VocA'))
