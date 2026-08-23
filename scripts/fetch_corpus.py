#!/usr/bin/env python3
"""
Download and parse the Quranic Arabic Corpus (morphology v0.4) from the
University of Leeds (http://corpus.quran.com), licensed under GPL.

Parses the tab-separated lines (chapter:verse:token:segment) and aggregates
the morphology of each word token into a JSON file.

Sources (in order of attempt):
  1. GitHub mirror: cltk/arabic_morphology_quranic-corpus
  2. Web mirror:    variatim.altervista.org
  3. Official:      corpus.quran.com/download
"""

import json
import os
import re
import sys
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "quranic_corpus_morphology.json")
CORPUS_PATH = os.path.join(BASE_DIR, "data", "quranic-corpus-morphology-0.4.txt")

SOURCES = [
    "https://raw.githubusercontent.com/cltk/arabic_morphology_quranic-corpus/master/quranic-corpus-morphology-0.4.txt",
    "http://variatim.altervista.org/VARCAR/quranic-corpus-morphology-0.4.txt",
]

# Features that carry a :value (POS:TYPE) vs plain tags (M, GEN, ...).
KEYED_FEATURES = {"POS", "LEM", "ROOT", "SP", "PRON"}
VERB_FEATURES = {
    "PERF": "aspect",
    "IMPF": "aspect",
    "IMPV": "aspect",
    "MOOD": "mood",
    "PASS": "voice",
    "I": "form",
    "II": "form",
    "III": "form",
    "IV": "form",
    "V": "form",
    "VI": "form",
    "VII": "form",
    "VIII": "form",
    "IX": "form",
    "X": "form",
    "XI": "form",
    "XII": "form",
    "XIII": "form",
    "XIV": "form",
    "XV": "form",
}
NOMINAL_FEATURES = {
    "M": "gender",
    "F": "gender",
    "MS": "number",
    "FS": "number",
    "MP": "number",
    "FP": "number",
    "D": "number",
    "S": "number",
    "NOM": "case",
    "ACC": "case",
    "GEN": "case",
    "DEF": "state",
    "INDEF": "state",
    "PCPL": "derivation",
    "VN": "derivation",
    "EMPH": "emphatic",
}
PERSON_FEATURES = {"1", "2", "3"}

TOKEN_RE = re.compile(r"^\((\d+):(\d+):(\d+):(\d+)\)\t(.*)$")


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuranDB/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            print(f"  FAILED: {url} - {e}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(2**attempt)
    return None


def download_corpus():
    if os.path.exists(CORPUS_PATH) and os.path.getsize(CORPUS_PATH) > 100_000:
        print(f"Using existing corpus file: {CORPUS_PATH}")
        return CORPUS_PATH

    for url in SOURCES:
        print(f"Downloading corpus from {url} ...")
        text = fetch(url)
        if text:
            with open(CORPUS_PATH, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved to {CORPUS_PATH} ({os.path.getsize(CORPUS_PATH)} bytes)")
            return CORPUS_PATH

    raise SystemExit(
        "Could not download the Quranic Arabic Corpus - run manually and retry."
    )


def parse_segment_features(features):
    """Parse the FEATURES column of a segment into a dict.

    Examples:
      STEM|POS:N|LEM:...|ROOT:...|M|GEN
      PREFIX|Al+
      SUFFIX|PRON:3MP
    """
    out = {}
    parts = features.split("|")
    if parts:
        out["role"] = parts[0]
    for feat in parts[1:]:
        if feat in KEYED_FEATURES:
            continue
        if ":" in feat:
            key, _, value = feat.partition(":")
            if key == "POS":
                out["pos"] = value
            elif key == "LEM":
                out["lemma"] = value
            elif key == "ROOT":
                out["root"] = value
            elif key == "SP":
                out["special"] = value
            elif key == "PRON":
                out["pron"] = value
        else:
            base = feat.rstrip("+")
            if base.startswith("(") and base.endswith(")"):
                out["form"] = base.strip("()")
            elif base in VERB_FEATURES:
                out[VERB_FEATURES[base]] = base
            elif base in NOMINAL_FEATURES:
                out[NOMINAL_FEATURES[base]] = base
            elif base in PERSON_FEATURES:
                out["person"] = base
            elif base == "ACT":
                out["voice"] = "ACT"
            elif base == "+VOC" or base == "VOC":
                out["vocative"] = True
            else:
                out.setdefault("other", []).append(base)
    return out


def parse_corpus(path):
    tokens = {}
    attributes = {}
    n_lines = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue

            if line.startswith("("):
                m = TOKEN_RE.match(line)
                if not m:
                    continue
                surah, ayah, token, segment = (int(g) for g in m.groups()[:4])
                form, tag, features = m.group(5).split("\t")
                n_lines += 1
                location = f"{surah}:{ayah}:{token}"
                seg = {
                    "form": form,
                    "tag": tag,
                    "features": parse_segment_features(features),
                }
                tokens.setdefault(location, {"segments": [], "tags": set()})
                tokens[location]["segments"].append(seg)
                tokens[location]["tags"].add(tag)
            elif line.startswith("V:"):
                # Verse attribute line: e.g. V:1:1   ... (not needed, kept for stats)
                parts = line.split("\t")
                attributes[parts[0]] = parts[1] if len(parts) > 1 else ""

    out = []
    for location, info in sorted(
        tokens.items(), key=lambda kv: [int(x) for x in kv[0].split(":")]
    ):
        stem = None
        for seg in info["segments"]:
            if seg["features"].get("role") == "STEM":
                stem = seg
                break
        if stem is None:
            stem = info["segments"][0]

        feats = stem["features"]
        entry = {
            "location": location,
            "pos": feats.get("pos"),
            "root": feats.get("root"),
            "lemma": feats.get("lemma"),
            "special": feats.get("special"),
            "form": feats.get("form"),
            "aspect": feats.get("aspect"),
            "mood": feats.get("mood"),
            "voice": feats.get("voice"),
            "person": feats.get("person"),
            "gender": feats.get("gender"),
            "number": feats.get("number"),
            "case": feats.get("case"),
            "state": feats.get("state"),
            "derivation": feats.get("derivation"),
            "segments": info["segments"],
        }
        out.append(entry)

    print(
        f"Parsed {len(out)} word tokens from {n_lines} segment lines ({len(attributes)} verse attributes)"
    )
    return out


def main():
    print("=== Fetching Quranic Arabic Corpus morphology (v0.4) ===\n")
    path = download_corpus()
    print("Parsing corpus...")
    data = parse_corpus(path)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"Saved {len(data)} tokens to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
