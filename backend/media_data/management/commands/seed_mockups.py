"""
Seed mockup records into the database.

Scans the MEDIA_ROOT/mockups/ directory for image files and creates
Mockup records if they don't already exist.

Expected filename convention:
    {garment}_{side}.{ext}
    e.g.: shirt_front.png, pants_back.svg

Usage:
    python manage.py seed_mockups
"""

import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from media_data.models import Mockup


class Command(BaseCommand):
    help = "Seed mockup records from files in the mockups directory."

    VALID_SIDES = {'FRONT', 'BACK'}

    def handle(self, *args, **options):
        mockups_dir = Path(settings.MEDIA_ROOT) / 'mockups'

        if not mockups_dir.exists():
            self.stderr.write(self.style.WARNING(
                f"Mockups directory does not exist: {mockups_dir}"
            ))
            return

        image_extensions = {'.png', '.jpg', '.jpeg', '.svg', '.webp'}
        files = [
            f for f in mockups_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
            and f.name not in ('.gitkeep', 'README.md')
        ]

        if not files:
            self.stdout.write(self.style.WARNING(
                "No image files found in mockups directory."
            ))
            return

        created = 0
        skipped = 0

        for filepath in sorted(files):
            name, side = self._parse_filename(filepath.stem)

            if name is None or side is None:
                self.stderr.write(self.style.WARNING(
                    f"Skipping '{filepath.name}': does not match "
                    "'garment_side' convention (e.g. shirt_front)"
                ))
                skipped += 1
                continue

            relative_path = f"mockups/{filepath.name}"

            if Mockup.objects.filter(
                name=name, side=side, image=relative_path
            ).exists():
                self.stdout.write(
                    f"  Already exists: {name} ({side})"
                )
                skipped += 1
                continue

            mockup = Mockup.objects.create(
                name=name,
                side=side,
                image=relative_path,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Created: {name} ({side})"
                )
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone: {created} created, {skipped} skipped."
            )
        )

    def _parse_filename(self, stem):
        """
        Parse 'garment_side' from filename stem.

        Returns (garment_name, side) or (None, None) if invalid.
        """
        parts = stem.rsplit('_', 1)
        if len(parts) != 2:
            return None, None

        garment_name, side = parts
        side_upper = side.upper()

        if side_upper not in self.VALID_SIDES:
            return None, None

        return garment_name, side_upper
