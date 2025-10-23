from pathlib import Path

text = Path('run.py').read_text()
start = text.index('        system = (')
end = text.index('\n        try:', start)
print(repr(text[start:end]))
