#!/usr/bin/env python3
"""
Word Error Rate (WER) Calculator for Speech-to-Text Evaluation

Computes WER, CER (Character Error Rate), and other STT quality metrics.

Usage:
    python benchmarks/wer_calculator.py --reference ref.txt --hypothesis hyp.txt
    python benchmarks/wer_calculator.py --batch --input results/transcriptions.json

Author: Claude Code (ORCHIDEA Framework v1.3)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class WERMetrics:
    """WER calculation results."""
    wer: float  # Word Error Rate (0-1)
    cer: float  # Character Error Rate (0-1)
    substitutions: int
    deletions: int
    insertions: int
    total_words: int
    total_chars: int
    sentence_count: int

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "wer": round(self.wer, 4),
            "wer_percent": round(self.wer * 100, 2),
            "cer": round(self.cer, 4),
            "cer_percent": round(self.cer * 100, 2),
            "substitutions": self.substitutions,
            "deletions": self.deletions,
            "insertions": self.insertions,
            "total_words": self.total_words,
            "total_chars": self.total_chars,
            "sentences": self.sentence_count
        }


def normalize_text(text: str) -> str:
    """
    Normalize text for fair WER comparison.

    Args:
        text: Input text

    Returns:
        Normalized text (lowercase, punctuation removed, normalized whitespace)
    """
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation (keep apostrophes for contractions)
    text = re.sub(r"[^\w\s']", " ", text)

    # Normalize whitespace
    text = " ".join(text.split())

    return text.strip()


def levenshtein_distance(ref: List[str], hyp: List[str]) -> Tuple[int, int, int, int]:
    """
    Calculate Levenshtein distance with operation counts.

    Args:
        ref: Reference word list
        hyp: Hypothesis word list

    Returns:
        (distance, substitutions, deletions, insertions)
    """
    n = len(ref)
    m = len(hyp)

    # Initialize DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    # Fill DP table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i-1] == hyp[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(
                    dp[i-1][j] + 1,    # Deletion
                    dp[i][j-1] + 1,    # Insertion
                    dp[i-1][j-1] + 1   # Substitution
                )

    # Backtrack to count operations
    i, j = n, m
    subs = dels = ins = 0

    while i > 0 or j > 0:
        if i == 0:
            ins += j
            break
        elif j == 0:
            dels += i
            break
        elif ref[i-1] == hyp[j-1]:
            i -= 1
            j -= 1
        else:
            if dp[i][j] == dp[i-1][j-1] + 1:
                subs += 1
                i -= 1
                j -= 1
            elif dp[i][j] == dp[i-1][j] + 1:
                dels += 1
                i -= 1
            else:
                ins += 1
                j -= 1

    return dp[n][m], subs, dels, ins


def calculate_wer(reference: str, hypothesis: str, normalize: bool = True) -> WERMetrics:
    """
    Calculate Word Error Rate (WER) and related metrics.

    Args:
        reference: Ground truth transcription
        hypothesis: Model transcription
        normalize: Apply text normalization (recommended: True)

    Returns:
        WERMetrics object
    """
    # Normalize if requested
    if normalize:
        reference = normalize_text(reference)
        hypothesis = normalize_text(hypothesis)

    # Split into words
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    # Calculate WER
    if len(ref_words) == 0:
        wer = 0.0 if len(hyp_words) == 0 else float('inf')
        return WERMetrics(
            wer=wer,
            cer=0.0,
            substitutions=0,
            deletions=0,
            insertions=len(hyp_words),
            total_words=0,
            total_chars=0,
            sentence_count=1
        )

    distance, subs, dels, ins = levenshtein_distance(ref_words, hyp_words)
    wer = distance / len(ref_words)

    # Calculate CER (Character Error Rate)
    ref_chars = list(reference.replace(" ", ""))
    hyp_chars = list(hypothesis.replace(" ", ""))

    if len(ref_chars) > 0:
        char_distance, _, _, _ = levenshtein_distance(ref_chars, hyp_chars)
        cer = char_distance / len(ref_chars)
    else:
        cer = 0.0

    return WERMetrics(
        wer=wer,
        cer=cer,
        substitutions=subs,
        deletions=dels,
        insertions=ins,
        total_words=len(ref_words),
        total_chars=len(ref_chars),
        sentence_count=1
    )


def calculate_batch_wer(pairs: List[Tuple[str, str]], normalize: bool = True) -> WERMetrics:
    """
    Calculate WER across multiple reference-hypothesis pairs.

    Args:
        pairs: List of (reference, hypothesis) tuples
        normalize: Apply text normalization

    Returns:
        Aggregated WERMetrics
    """
    total_subs = total_dels = total_ins = 0
    total_words = total_chars = 0

    for ref, hyp in pairs:
        metrics = calculate_wer(ref, hyp, normalize=normalize)
        total_subs += metrics.substitutions
        total_dels += metrics.deletions
        total_ins += metrics.insertions
        total_words += metrics.total_words
        total_chars += metrics.total_chars

    # Aggregate WER
    total_distance = total_subs + total_dels + total_ins
    wer = total_distance / total_words if total_words > 0 else 0.0

    # Aggregate CER (approximate)
    cer = sum(calculate_wer(r, h, normalize).cer for r, h in pairs) / len(pairs) if pairs else 0.0

    return WERMetrics(
        wer=wer,
        cer=cer,
        substitutions=total_subs,
        deletions=total_dels,
        insertions=total_ins,
        total_words=total_words,
        total_chars=total_chars,
        sentence_count=len(pairs)
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate Word Error Rate (WER) for STT evaluation"
    )
    parser.add_argument(
        "--reference",
        type=Path,
        help="Reference transcription file"
    )
    parser.add_argument(
        "--hypothesis",
        type=Path,
        help="Hypothesis transcription file"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: process JSON file with multiple pairs"
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Input JSON file for batch mode (format: [{\"reference\": \"...\", \"hypothesis\": \"...\"}])"
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable text normalization"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file for results"
    )

    args = parser.parse_args()

    normalize = not args.no_normalize

    # Batch mode
    if args.batch:
        if not args.input:
            print("❌ Error: --input required for batch mode", file=sys.stderr)
            return 1

        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        pairs = [(item["reference"], item["hypothesis"]) for item in data]
        metrics = calculate_batch_wer(pairs, normalize=normalize)

        print("=" * 60)
        print("Batch WER Results")
        print("=" * 60)
        print(f"WER: {metrics.wer:.4f} ({metrics.wer * 100:.2f}%)")
        print(f"CER: {metrics.cer:.4f} ({metrics.cer * 100:.2f}%)")
        print(f"Substitutions: {metrics.substitutions}")
        print(f"Deletions: {metrics.deletions}")
        print(f"Insertions: {metrics.insertions}")
        print(f"Total words: {metrics.total_words}")
        print(f"Total sentences: {metrics.sentence_count}")
        print("=" * 60)

    # Single pair mode
    else:
        if not args.reference or not args.hypothesis:
            print("❌ Error: --reference and --hypothesis required", file=sys.stderr)
            return 1

        with open(args.reference, "r", encoding="utf-8") as f:
            reference = f.read().strip()

        with open(args.hypothesis, "r", encoding="utf-8") as f:
            hypothesis = f.read().strip()

        metrics = calculate_wer(reference, hypothesis, normalize=normalize)

        print("=" * 60)
        print("WER Results")
        print("=" * 60)
        print(f"Reference: {reference}")
        print(f"Hypothesis: {hypothesis}")
        print()
        print(f"WER: {metrics.wer:.4f} ({metrics.wer * 100:.2f}%)")
        print(f"CER: {metrics.cer:.4f} ({metrics.cer * 100:.2f}%)")
        print(f"Substitutions: {metrics.substitutions}")
        print(f"Deletions: {metrics.deletions}")
        print(f"Insertions: {metrics.insertions}")
        print("=" * 60)

    # Output to JSON if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(metrics.to_dict(), f, indent=2)
        print(f"\nResults saved to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
