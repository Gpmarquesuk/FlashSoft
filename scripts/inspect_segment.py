from pathlib import Path
text = Path('run.py').read_text()
start = text.index('Current file contents:')
segment = text[start:start+30]
print(segment)
print([ord(c) for c in segment])
