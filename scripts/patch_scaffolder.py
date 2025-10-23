from pathlib import Path

path = Path('tools/scaffolder.py')
text = path.read_text(encoding='utf-8')
old = "    try:\n        validate_plan(plan)\n    except ValueError as exc:\n        summary[\"errors\"].append(str(exc))\n        return summary\n\n    base_dir = Path(base_path)"
new = "    validate_plan(plan)\n\n    base_dir = Path(base_path)"
if old not in text:
    raise SystemExit('validate block not found')
text = text.replace(old, new, 1)
text = text.replace(
    "        return str(target.relative_to(base))",
    "        return str(target.relative_to(base)).replace('\\\\', '/')",
)
text = text.replace(
    "        return str(target)",
    "        return str(target).replace('\\\\', '/')",
)
path.write_text(text, encoding='utf-8')
