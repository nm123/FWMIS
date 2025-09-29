#!/usr/bin/env python3
"""
Database Archiving System for FWMIS

This module provides comprehensive database archiving functionality including:
- Case archiving based on financial year and status
- Archive retrieval and restoration
- Archive storage management
- Performance monitoring and cleanup
- Automated archiving policies
"""

import hashlib
import json
import os
import shutil
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from scripts.Utilities.config import DB_PATH


class DatabaseArchiver:
    """Comprehensive database archiving system for FWMIS"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = Path(db_path)
        self.archive_dir = self.db_path.parent / "archives"
        self.archive_dir.mkdir(exist_ok=True)

        # Archive configuration
        self.config = {
            "max_cases_per_archive": 10000,
            "archive_finalized_only": True,
            "retention_years": 7,
            "auto_archive_threshold": 50000,
            "compression_enabled": True,
        }

    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics for archiving decisions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            stats = {}

            # Overall statistics
            cursor.execute("SELECT COUNT(*) FROM cases")
            stats["total_cases"] = cursor.fetchone()[0]

            # Cases by financial year
            cursor.execute(
                """
                SELECT printf('%d-%d', fy.start_year, fy.end_year) as fy_year, COUNT(c.id)
                FROM cases c
                JOIN financial_years fy ON c.fy_id = fy.id
                GROUP BY fy_year
                ORDER BY fy.start_year, fy.end_year
            """
            )
            stats["cases_by_fy"] = dict(cursor.fetchall())

            # Cases by status
            cursor.execute(
                """
                SELECT assessment_status, COUNT(*)
                FROM cases
                GROUP BY assessment_status
            """
            )
            stats["cases_by_status"] = dict(cursor.fetchall())

            # Finalized cases by financial year
            cursor.execute(
                """
                SELECT printf('%d-%d', fy.start_year, fy.end_year) as fy_year, COUNT(c.id)
                FROM cases c
                JOIN financial_years fy ON c.fy_id = fy.id
                WHERE c.is_finalized = 1
                GROUP BY fy_year
                ORDER BY fy.start_year, fy.end_year
            """
            )
            stats["finalized_by_fy"] = dict(cursor.fetchall())

            # Cases by age (years since identification)
            cursor.execute(
                """
                SELECT
                    CASE
                        WHEN julianday('now') - julianday(date_identified) < 365 THEN 'current_year'
                        WHEN julianday('now') - julianday(date_identified) < 730 THEN '1_year_old'
                        WHEN julianday('now') - julianday(date_identified) < 1095 THEN '2_years_old'
                        ELSE 'older'
                    END as age_group,
                    COUNT(*) as count
                FROM cases
                WHERE date_identified IS NOT NULL
                GROUP BY age_group
            """
            )
            stats["cases_by_age"] = dict(cursor.fetchall())

            # Database size
            stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)

            # Archive statistics
            archive_files = list(self.archive_dir.glob("*.archive"))
            stats["archive_count"] = len(archive_files)
            stats["total_archive_size_mb"] = sum(
                f.stat().st_size for f in archive_files
            ) / (1024 * 1024)

            return stats

        finally:
            conn.close()

    def create_archive(
        self, fy_year: str, archive_type: str = "auto"
    ) -> Tuple[bool, str]:
        """
        Create an archive for a specific financial year

        Args:
            fy_year: Financial year to archive (e.g., "2022-2023")
            archive_type: Type of archive ("auto", "manual", "emergency")

        Returns:
            Tuple of (success, message)
        """
        print(f"🗄️  Creating archive for financial year {fy_year}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Verify financial year exists and get its ID
            # fy_year comes in as "start_year-end_year" format (e.g., "2022-2023")
            try:
                start_year, end_year = fy_year.split("-")
                start_year, end_year = int(start_year), int(end_year)
            except ValueError:
                return (
                    False,
                    f"Invalid financial year format: {fy_year}. Expected format: start_year-end_year (e.g., 2022-2023)",
                )

            cursor.execute(
                "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
                (start_year, end_year),
            )
            fy_result = cursor.fetchone()
            if not fy_result:
                return False, f"Financial year {fy_year} not found in database"

            fy_id = fy_result[0]

            # Get cases to archive (only finalized cases for safety)
            cursor.execute(
                """
                SELECT COUNT(*) FROM cases
                WHERE fy_id = ? AND is_finalized = 1
            """,
                (fy_id,),
            )
            case_count = cursor.fetchone()[0]

            if case_count == 0:
                return False, f"No finalized cases found for financial year {fy_year}"

            print(f"📊 Found {case_count} finalized cases to archive")

            # Create archive metadata
            archive_id = f"{fy_year}_{int(time.time())}_{archive_type}"
            archive_file = self.archive_dir / f"{archive_id}.archive"

            archive_metadata = {
                "archive_id": archive_id,
                "financial_year": fy_year,
                "fy_id": fy_id,
                "created_at": datetime.now().isoformat(),
                "archive_type": archive_type,
                "case_count": case_count,
                "database_version": "1.0",
                "compression": self.config["compression_enabled"],
            }

            # Export cases to archive
            cursor.execute(
                """
                SELECT * FROM cases WHERE fy_id = ? AND is_finalized = 1
            """,
                (fy_id,),
            )
            cases_data = cursor.fetchall()

            # Get column names
            cursor.execute("PRAGMA table_info(cases)")
            columns = [col[1] for col in cursor.fetchall()]

            archive_data = {
                "metadata": archive_metadata,
                "columns": columns,
                "cases": cases_data,
            }

            # Write archive file
            with open(archive_file, "w", encoding="utf-8") as f:
                json.dump(archive_data, f, indent=2, default=str)

            print(f"💾 Archive created: {archive_file}")

            # Calculate archive size
            archive_size_mb = archive_file.stat().st_size / (1024 * 1024)

            # Create checksum for integrity verification
            with open(archive_file, "rb") as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Update metadata with size and checksum
            archive_metadata.update(
                {"file_size_mb": round(archive_size_mb, 2), "checksum_sha256": checksum}
            )

            # Rewrite metadata
            with open(archive_file, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["metadata"] = archive_metadata
                f.seek(0)
                json.dump(data, f, indent=2, default=str)
                f.truncate()

            # Optionally remove archived cases from main database
            if archive_type in ["manual", "emergency"]:  # Only for explicit archiving
                print(f"🗑️  Removing {case_count} cases from main database...")
                cursor.execute(
                    "DELETE FROM cases WHERE fy_id = ? AND is_finalized = 1", (fy_id,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                print(f"✅ Removed {deleted_count} cases from main database")

            # Vacuum database to reclaim space
            print("🧹 Optimizing database after archiving...")
            cursor.execute("VACUUM")
            conn.commit()

            success_msg = (
                f"✅ Archive created successfully!\n"
                f"   Archive ID: {archive_id}\n"
                f"   Cases archived: {case_count}\n"
                f"   File size: {archive_size_mb:.2f} MB\n"
                f"   Location: {archive_file}"
            )

            return True, success_msg

        except Exception as e:
            conn.rollback()
            return False, f"Archive creation failed: {e}"

        finally:
            conn.close()

    def list_archives(self) -> List[Dict]:
        """List all available archives with metadata"""
        archives = []

        for archive_file in self.archive_dir.glob("*.archive"):
            try:
                with open(archive_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("metadata", {})
                metadata["file_path"] = str(archive_file)
                metadata["file_size_mb"] = archive_file.stat().st_size / (1024 * 1024)

                archives.append(metadata)

            except Exception as e:
                # Handle corrupted archive files
                archives.append(
                    {
                        "archive_id": archive_file.stem,
                        "error": f"Corrupted archive: {e}",
                        "file_path": str(archive_file),
                        "file_size_mb": archive_file.stat().st_size / (1024 * 1024),
                    }
                )

        # Sort by creation date (newest first)
        archives.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return archives

    def restore_archive(self, archive_id: str) -> Tuple[bool, str]:
        """
        Restore cases from an archive back to the main database

        Args:
            archive_id: ID of the archive to restore

        Returns:
            Tuple of (success, message)
        """
        print(f"🔄 Restoring archive: {archive_id}")

        archive_file = self.archive_dir / f"{archive_id}.archive"

        if not archive_file.exists():
            return False, f"Archive file not found: {archive_file}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Read archive data
            with open(archive_file, "r", encoding="utf-8") as f:
                archive_data = json.load(f)

            metadata = archive_data.get("metadata", {})
            columns = archive_data.get("columns", [])
            cases = archive_data.get("cases", [])

            if not cases:
                return False, "Archive contains no cases to restore"

            print(f"📊 Restoring {len(cases)} cases from archive")

            # Verify financial year still exists or create it
            fy_year = metadata.get("financial_year")
            if fy_year:
                try:
                    start_year, end_year = fy_year.split("-")
                    start_year, end_year = int(start_year), int(end_year)
                except ValueError:
                    return False, f"Invalid financial year format in archive: {fy_year}"

                cursor.execute(
                    "SELECT id FROM financial_years WHERE start_year = ? AND end_year = ?",
                    (start_year, end_year),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO financial_years (start_year, end_year, status, active_period) VALUES (?, ?, 'closed', 0)",
                        (start_year, end_year),
                    )
                    print(f"✅ Created financial year: {fy_year}")

            # Insert cases (skip if they already exist)
            restored_count = 0
            skipped_count = 0

            for case_data in cases:
                try:
                    # Create parameter placeholders
                    placeholders = ",".join(["?"] * len(case_data))
                    query = f"INSERT OR IGNORE INTO cases ({','.join(columns)}) VALUES ({placeholders})"

                    cursor.execute(query, case_data)
                    if cursor.rowcount > 0:
                        restored_count += 1
                    else:
                        skipped_count += 1

                except Exception as e:
                    print(f"⚠️  Failed to restore case: {e}")
                    continue

            conn.commit()

            success_msg = (
                f"✅ Archive restored successfully!\n"
                f"   Archive ID: {archive_id}\n"
                f"   Cases restored: {restored_count}\n"
                f"   Cases skipped (already exist): {skipped_count}\n"
                f"   Total processed: {len(cases)}"
            )

            return True, success_msg

        except Exception as e:
            conn.rollback()
            return False, f"Archive restoration failed: {e}"

        finally:
            conn.close()

    def delete_archive(
        self, archive_id: str, confirm: bool = False
    ) -> Tuple[bool, str]:
        """
        Permanently delete an archive

        Args:
            archive_id: ID of archive to delete
            confirm: Must be True to actually delete

        Returns:
            Tuple of (success, message)
        """
        if not confirm:
            return False, "Archive deletion requires explicit confirmation"

        archive_file = self.archive_dir / f"{archive_id}.archive"

        if not archive_file.exists():
            return False, f"Archive file not found: {archive_file}"

        try:
            # Get archive info before deletion
            with open(archive_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                case_count = data.get("metadata", {}).get("case_count", 0)

            # Delete the file
            archive_file.unlink()

            return (
                True,
                f"✅ Archive {archive_id} deleted successfully ({case_count} cases)",
            )

        except Exception as e:
            return False, f"Archive deletion failed: {e}"

    def get_archiving_recommendations(self) -> List[str]:
        """Get intelligent archiving recommendations based on current database state"""
        recommendations = []
        stats = self.get_database_stats()

        total_cases = stats.get("total_cases", 0)
        finalized_cases = sum(stats.get("finalized_by_fy", {}).values())

        # Check total case count
        if total_cases > self.config["auto_archive_threshold"]:
            recommendations.append(
                f"🔴 CRITICAL: Database has {total_cases:,} cases "
                f"(threshold: {self.config['auto_archive_threshold']:,}). "
                "Immediate archiving recommended."
            )

        elif total_cases > 25000:
            recommendations.append(
                f"🟡 WARNING: Database has {total_cases:,} cases. "
                "Consider archiving completed financial years."
            )

        # Check finalization rate
        if finalized_cases > 0:
            finalization_rate = finalized_cases / total_cases
            if finalization_rate > 0.8:
                recommendations.append(
                    ".1%" "Excellent finalization rate - good candidates for archiving."
                )
            elif finalization_rate < 0.2:
                recommendations.append(
                    ".1%"
                    "Low finalization rate - focus on completing workflows before archiving."
                )

        # Check cases by financial year
        cases_by_fy = stats.get("cases_by_fy", {})
        finalized_by_fy = stats.get("finalized_by_fy", {})

        current_year = datetime.now().year
        current_fy = f"{current_year}-{current_year + 1}"

        # Recommend archiving old, fully finalized financial years
        for fy_year, fy_cases in cases_by_fy.items():
            finalized = finalized_by_fy.get(fy_year, 0)

            if fy_year != current_fy and finalized == fy_cases and fy_cases > 100:
                recommendations.append(
                    f"✅ RECOMMEND: Archive FY {fy_year} "
                    f"({finalized:,} finalized cases - 100% complete)"
                )

        # Check archive storage
        archive_count = stats.get("archive_count", 0)
        if archive_count == 0:
            recommendations.append(
                "ℹ️  INFO: No archives exist yet. Consider setting up regular archiving."
            )
        elif archive_count > 10:
            recommendations.append(
                f"ℹ️  INFO: {archive_count} archives exist. Consider archive consolidation."
            )

        return recommendations

    def auto_archive_check(self) -> List[str]:
        """Check if automatic archiving should be triggered"""
        actions = []
        stats = self.get_database_stats()

        total_cases = stats.get("total_cases", 0)

        if total_cases > self.config["auto_archive_threshold"]:
            # Find oldest fully finalized financial year to archive
            finalized_by_fy = stats.get("finalized_by_fy", {})
            cases_by_fy = stats.get("cases_by_fy", {})

            for fy_year in sorted(finalized_by_fy.keys()):
                if (
                    finalized_by_fy[fy_year] == cases_by_fy.get(fy_year, 0)
                    and cases_by_fy[fy_year] > self.config["max_cases_per_archive"] // 2
                ):

                    actions.append(fy_year)
                    break  # Only auto-archive one FY at a time

        return actions


def archive_database_cli():
    """Command-line interface for database archiving"""
    import argparse

    parser = argparse.ArgumentParser(description="FWMIS Database Archiving System")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument(
        "--recommendations", action="store_true", help="Show archiving recommendations"
    )
    parser.add_argument(
        "--list-archives", action="store_true", help="List all archives"
    )
    parser.add_argument(
        "--create-archive", help="Create archive for financial year (e.g., '2022-2023')"
    )
    parser.add_argument("--restore-archive", help="Restore archive by ID")
    parser.add_argument("--delete-archive", help="Delete archive by ID")
    parser.add_argument(
        "--confirm-delete", action="store_true", help="Confirm archive deletion"
    )
    parser.add_argument(
        "--auto-check", action="store_true", help="Check if auto-archiving should run"
    )

    args = parser.parse_args()

    archiver = DatabaseArchiver()

    if args.stats:
        print("📊 DATABASE STATISTICS:")
        stats = archiver.get_database_stats()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value:,}")
            else:
                print(f"  {key}: {value}")
        print()

    if args.recommendations:
        print("💡 ARCHIVING RECOMMENDATIONS:")
        recommendations = archiver.get_archiving_recommendations()
        for rec in recommendations:
            print(f"  {rec}")
        print()

    if args.list_archives:
        print("🗄️  ARCHIVE LIST:")
        archives = archiver.list_archives()
        if not archives:
            print("  No archives found.")
        else:
            for archive in archives:
                status = "✅ OK" if "error" not in archive else f"❌ {archive['error']}"
                print(
                    f"  {archive['archive_id']}: {archive.get('case_count', 'N/A')} cases, "
                    f"{archive.get('file_size_mb', 0):.1f} MB - {status}"
                )
        print()

    if args.create_archive:
        success, message = archiver.create_archive(args.create_archive, "manual")
        if success:
            print("✅ " + message)
        else:
            print("❌ " + message)

    if args.restore_archive:
        success, message = archiver.restore_archive(args.restore_archive)
        if success:
            print("✅ " + message)
        else:
            print("❌ " + message)

    if args.delete_archive:
        if not args.confirm_delete:
            print("❌ Archive deletion requires --confirm-delete flag for safety")
            return

        success, message = archiver.delete_archive(args.delete_archive, confirm=True)
        if success:
            print("✅ " + message)
        else:
            print("❌ " + message)

    if args.auto_check:
        print("🤖 AUTO-ARCHIVE CHECK:")
        auto_targets = archiver.auto_archive_check()
        if auto_targets:
            print(f"  Auto-archiving recommended for: {', '.join(auto_targets)}")
            for fy_year in auto_targets:
                success, message = archiver.create_archive(fy_year, "auto")
                if success:
                    print(f"  ✅ Auto-archived {fy_year}")
                else:
                    print(f"  ❌ Failed to auto-archive {fy_year}: {message}")
        else:
            print("  No auto-archiving needed at this time.")
        print()

    if not any(
        [
            args.stats,
            args.recommendations,
            args.list_archives,
            args.create_archive,
            args.restore_archive,
            args.delete_archive,
            args.auto_check,
        ]
    ):
        parser.print_help()


if __name__ == "__main__":
    archive_database_cli()
