#!/usr/bin/env python3
"""
Extrait les chaînes UTF-16 little endian d'un fichier .loo (format .loo).
Usage: python extract_loo_strings.py [chemin_vers_fichier.loo]
"""
import sys
import re
from typing import List

def extract_utf16le_strings(path: str, min_length: int = 3) -> List[str]:
    with open(path, "rb") as f:
        data = f.read()
    strings = []
    i = 0
    while i < len(data) - 1:
        if data[i + 1] == 0 and 32 <= data[i] < 127:
            start = i
            i += 2
            while i < len(data) - 1 and data[i + 1] == 0 and data[i] != 0 and (32 <= data[i] < 127 or data[i] in (9, 10, 13)):
                i += 2
            s = data[start:i].decode("utf-16-le", errors="ignore").strip()
            if len(s) >= min_length and not re.match(r"^[\x00-\x1f]+$", s):
                strings.append(s)
        else:
            i += 1
    return strings

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "samples/N_MCD_ECF4_MediaT.loo"
    for s in extract_utf16le_strings(path):
        print(s)

if __name__ == "__main__":
    main()
