#!/usr/bin/env python3

"""Removes temporary Sphinx build artifacts to ensure a clean build.

This is needed if the Python source being documented changes significantly. Old sphinx-apidoc
RST files can be left behind.
"""

import shutil
from pathlib import Path


def main() -> None:
    docs_dir = Path(__file__).resolve().parent
    root_dir = docs_dir.parent

    # Clean build directories
    for folder in ('_build', 'apidoc'):
        delete_dir = docs_dir / folder
        if delete_dir.exists():
            shutil.rmtree(delete_dir)

    # Create readme.rst from README.md if it exists
    readme_md = root_dir / 'README.md'
    readme_rst = docs_dir / 'readme.rst'

    if readme_md.exists():
        # Create a simple RST file that references the markdown
        # For now, just create a placeholder that can be manually converted
        if not readme_rst.exists():
            readme_rst.write_text(
                'README\n'
                '======\n\n'
                '.. note::\n\n'
                '   The full README is available in Markdown format.\n'
                '   See `README.md <../README.md>`_ in the project root.\n\n'
                'For installation and usage instructions, please refer to the\n'
                '`README.md <../README.md>`_ file in the project root directory.\n'
            )


if __name__ == '__main__':
    main()
