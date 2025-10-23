import re
import pathlib

root = pathlib.Path('docs')

def extract_first_code_block(path: pathlib.Path) -> str:
    text = path.read_text(encoding='utf-8')
    match = re.search(r"```python\n([\s\S]+?)```", text)
    if not match:
        raise ValueError(f"No python block found in {path}")
    return match.group(1).strip()

# scaffolder module
scaffolder_code = extract_first_code_block(root / 'scaffolder_module.md')
tools_dir = pathlib.Path('tools')
tools_dir.mkdir(exist_ok=True)
(tls_file := tools_dir / 'scaffolder.py').write_text(scaffolder_code + '\n', encoding='utf-8')

# scaffolder tests
scaffolder_tests = extract_first_code_block(root / 'scaffolder_tests.md')
tests_dir = pathlib.Path('tests')
tests_dir.mkdir(exist_ok=True)
(tests_dir / 'test_scaffolder.py').write_text(scaffolder_tests + '\n', encoding='utf-8')

# json utils and tests
text = (root / 'json_validation_helpers.md').read_text(encoding='utf-8')
blocks = re.findall(r"```python\n([\s\S]+?)```", text)
if len(blocks) < 2:
    raise ValueError('Expected two python blocks in json_validation_helpers.md')
utils_code, json_tests_code = (block.strip() for block in blocks[:2])
utils_dir = pathlib.Path('utils')
utils_dir.mkdir(exist_ok=True)
(utils_dir / 'json_validation.py').write_text(utils_code + '\n', encoding='utf-8')
(tests_dir / 'test_json_validation.py').write_text(json_tests_code + '\n', encoding='utf-8')

# task decomposer prompt
prompt_text = (root / 'task_decomposer_prompt.md').read_text(encoding='utf-8')
prompts_dir = pathlib.Path('prompts')
prompts_dir.mkdir(exist_ok=True)
(prompts_dir / 'task_decomposer.md').write_text(prompt_text, encoding='utf-8')

print('Artifacts materialized successfully.')
