# FileHound

A local duplicate-file finder. It groups files by size first, then compares SHA-256 hashes so files with the same name but different contents are not treated as duplicates.

## Requirements

Python 3.10+. No dependencies.

## Usage

```bash
python filehound.py "D:/Photos" "D:/Downloads"
python filehound.py ./files --min-size 1024 --csv duplicates.csv
python filehound.py ./files --include-hidden
```

The tool only reads files. It does not delete, move, or modify anything. Symbolic links are skipped to avoid walking outside the folders you selected. The CSV report contains the hash, file size, and paths for each duplicate group.

## Tests

```bash
python -m unittest discover -s tests -v
```

MIT License.
