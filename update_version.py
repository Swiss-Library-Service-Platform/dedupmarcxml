import os
import re
import dedupmarcxml

version = dedupmarcxml.__version__
commit_message = dedupmarcxml.commit_message

# pyproject.toml
with open('pyproject.toml') as f:
    content = f.read()

if re.search(r'version = "(.+)"', content).group(1) == version:
    print('The version is already up to date')
    exit()

content = re.sub(r'version = ".+"', f'version = "{version}"', content)

with open('pyproject.toml', 'w') as f:
    f.write(content)

# docs/conf.py
with open('docs/conf.py') as f:
    content = f.read()

content = re.sub(r'version = ".+"', f'version = "{version}"', content)

with open('docs/conf.py', 'w') as f:
    f.write(content)


# # index.rst
# with open('docs/index.rst') as f:
#     content = f.read()
#
# content = re.sub(r'\* Version: \d+\.\d+\.\d+', f'* Version: {version}', content)
#
# with open('docs/index.rst', 'w') as f:
#     f.write(content)

# Build the new doc
os.system(f'{os.getcwd()}/docs/make.bat html')
os.system(f'{os.getcwd()}/docs/make.bat html')

# Delete all files of dist folder
files = os.listdir('dist')
for f in files:
    os.remove(f'dist/{f}')

# Build the new package
os.system('python -m build')

# Commit the new version
os.system('git add .')
os.system(f'git commit -m "{commit_message} - Create version {version}"')
os.system(f'git push')

# Upload the package on pipy
os.system('python -m twine upload dist/*')
