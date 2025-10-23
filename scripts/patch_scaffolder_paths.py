from pathlib import Path

path = Path('tools/scaffolder.py')
text = path.read_text(encoding='utf-8')
text = text.replace("return str(target.relative_to(base)).replace('\\\\', '/')", "return str(target.relative_to(base)).replace('\\\\', '/').replace('\\', '/')")
text = text.replace("return str(target).replace('\\\\', '/')", "return str(target).replace('\\\\', '/').replace('\\', '/')")
path.write_text(text, encoding='utf-8')
