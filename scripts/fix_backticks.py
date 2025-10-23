from pathlib import Path
text = Path('run.py').read_text()
text = text.replace("Current file contents:\npython", "Current file contents:\n`python")
text = text.replace("\n\n\"\n            \"Return the corrected file enclosed in python", "`\n\n\"\n            \"Return the corrected file enclosed in `python`")
Path('run.py').write_text(text)
