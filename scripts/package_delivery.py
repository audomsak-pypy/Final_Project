"""Package tracked source + generated data + test evidence, excluding environments and credentials."""
from pathlib import Path
import subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
output=ROOT.parent/'adidur-delivery.zip'
files=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().strip('\x00').split('\x00'))
files.add('scripts/package_delivery.py')
for folder in ['data','tests/artifacts']:
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:files.add(str(path.relative_to(ROOT)))
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for name in sorted(files):
        if (ROOT/name).is_file():z.write(ROOT/name,'Adidur/'+name)
print(f'{output}: {output.stat().st_size:,} bytes; {len(files)} files')
