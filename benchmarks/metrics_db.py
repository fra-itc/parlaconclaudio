#!/usr/bin/env python3
"""
Metrics Database Manager for RTSTT Benchmarking

SQLite database for storing benchmark results, model comparisons, and hyperparameter experiments.

Tables:
- models: Model configurations and metadata
- benchmarks: Individual benchmark runs
- hyperparameters: Hyperparameter experiment results
- comparisons: Model comparison snapshots

Usage:
    python benchmarks/metrics_db.py --init
    python benchmarks/metrics_db.py --export-all --format csv --output-dir exports/

Author: Claude Code (ORCHIDEA Framework v1.3)
"""

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ModelRecord:
    """Model configuration record."""
    model_id: str
    model_name: str
    model_type: str  # whisper, llama, nlp
    variant: str  # large-v3, medium, 3b-8bit, etc.
    compute_type: str  # fp16, int8, 4bit
    memory_requirement_mb: int
    created_at: str


@dataclass
class BenchmarkRecord:
    """Benchmark result record."""
    benchmark_id: str
    model_id: str
    test_set: str
    test_date: str

    # STT metrics
    wer: Optional[float] = None
    cer: Optional[float] = None

    # LLM metrics
    rouge_1: Optional[float] = None
    rouge_2: Optional[float] = None
    rouge_l: Optional[float] = None

    # NLP metrics
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None

    # Performance metrics
    latency_p50_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    latency_p99_ms: Optional[float] = None
    throughput_rtf: Optional[float] = None
    tokens_per_sec: Optional[float] = None

    # Resource metrics
    gpu_memory_mb: Optional[int] = None
    gpu_utilization_pct: Optional[float] = None
    cpu_utilization_pct: Optional[float] = None

    # Test metadata
    num_samples: int = 0
    total_duration_sec: Optional[float] = None
    notes: Optional[str] = None


class MetricsDB:
    """SQLite database manager for benchmark metrics."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "benchmarks/metrics.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self.conn.cursor()

        # Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                variant TEXT NOT NULL,
                compute_type TEXT NOT NULL,
                memory_requirement_mb INTEGER,
                created_at TEXT NOT NULL,
                UNIQUE(model_name, variant, compute_type)
            )
        """)

        # Benchmarks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                benchmark_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                test_set TEXT NOT NULL,
                test_date TEXT NOT NULL,

                wer REAL,
                cer REAL,
                rouge_1 REAL,
                rouge_2 REAL,
                rouge_l REAL,
                precision REAL,
                recall REAL,
                f1_score REAL,

                latency_p50_ms REAL,
                latency_p95_ms REAL,
                latency_p99_ms REAL,
                throughput_rtf REAL,
                tokens_per_sec REAL,

                gpu_memory_mb INTEGER,
                gpu_utilization_pct REAL,
                cpu_utilization_pct REAL,

                num_samples INTEGER DEFAULT 0,
                total_duration_sec REAL,
                notes TEXT,

                FOREIGN KEY (model_id) REFERENCES models(model_id)
            )
        """)

        # Hyperparameters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hyperparameters (
                experiment_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                experiment_date TEXT NOT NULL,

                FOREIGN KEY (model_id) REFERENCES models(model_id)
            )
        """)

        # Comparisons table (snapshots of comparison results)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparisons (
                comparison_id TEXT PRIMARY KEY,
                comparison_name TEXT NOT NULL,
                model_ids TEXT NOT NULL,  -- JSON array
                comparison_data TEXT NOT NULL,  -- JSON object
                created_at TEXT NOT NULL
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmarks_model_id ON benchmarks(model_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmarks_test_set ON benchmarks(test_set)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hyperparameters_model_id ON hyperparameters(model_id)")

        # Metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("schema_version", str(self.SCHEMA_VERSION))
        )

        self.conn.commit()
        print(f"✅ Database schema initialized: {self.db_path}")
        print(f"   Schema version: {self.SCHEMA_VERSION}")

    def insert_model(self, model: ModelRecord) -> None:
        """Insert model record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO models
            (model_id, model_name, model_type, variant, compute_type, memory_requirement_mb, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            model.model_id,
            model.model_name,
            model.model_type,
            model.variant,
            model.compute_type,
            model.memory_requirement_mb,
            model.created_at
        ))
        self.conn.commit()

    def insert_benchmark(self, benchmark: BenchmarkRecord) -> None:
        """Insert benchmark record."""
        data = asdict(benchmark)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))

        cursor = self.conn.cursor()
        cursor.execute(
            f"INSERT OR REPLACE INTO benchmarks ({columns}) VALUES ({placeholders})",
            tuple(data.values())
        )
        self.conn.commit()

    def get_benchmarks_by_model(self, model_id: str) -> List[Dict[str, Any]]:
        """Get all benchmarks for a model."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM benchmarks WHERE model_id = ? ORDER BY test_date DESC",
            (model_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_latest_benchmark(self, model_id: str, test_set: str) -> Optional[Dict[str, Any]]:
        """Get latest benchmark for model and test set."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM benchmarks
            WHERE model_id = ? AND test_set = ?
            ORDER BY test_date DESC
            LIMIT 1
        """, (model_id, test_set))

        row = cursor.fetchone()
        return dict(row) if row else None

    def export_to_csv(self, table: str, output_path: Path) -> None:
        """Export table to CSV."""
        import csv

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")

        rows = cursor.fetchall()
        if not rows:
            print(f"⚠️  No data in table {table}")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cursor.description])
            writer.writerows(rows)

        print(f"✅ Exported {len(rows)} rows to {output_path}")

    def export_all_to_csv(self, output_dir: Path) -> None:
        """Export all tables to CSV files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        tables = ["models", "benchmarks", "hyperparameters", "comparisons"]
        for table in tables:
            self.export_to_csv(table, output_dir / f"{table}.csv")

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Metrics Database Manager for RTSTT Benchmarking"
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="benchmarks/metrics.db",
        help="Database file path (default: benchmarks/metrics.db)"
    )

    # Actions
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize database schema"
    )
    parser.add_argument(
        "--export-all",
        action="store_true",
        help="Export all tables to CSV"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="csv",
        choices=["csv"],
        help="Export format (default: csv)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("exports"),
        help="Output directory for exports (default: exports/)"
    )

    args = parser.parse_args()

    # Initialize database
    db = MetricsDB(db_path=args.db_path)

    try:
        if args.init:
            db.init_schema()

        if args.export_all:
            db.export_all_to_csv(args.output_dir)

        if not any([args.init, args.export_all]):
            # Default: show schema
            cursor = db.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]

            print("=" * 60)
            print("RTSTT Metrics Database")
            print("=" * 60)
            print(f"Database: {args.db_path}")
            print(f"Tables: {', '.join(tables)}")
            print("=" * 60)

            for table in tables:
                if table == 'metadata':
                    continue
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} records")

    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
