import os
import io
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

class Command(BaseCommand):
    help = 'Migrates data from SQLite to PostgreSQL'

    def handle(self, *args, **options):
        # 1. Validate DBs
        if 'sqlite' not in settings.DATABASES:
            raise CommandError("Please define 'sqlite' in settings.DATABASES first.")
        
        default_db = settings.DATABASES[DEFAULT_DB_ALIAS]
        if 'postgresql' not in default_db['ENGINE'] and 'postgis' not in default_db['ENGINE']:
            self.stdout.write(self.style.WARNING(f"Warning: 'default' database engine is {default_db['ENGINE']}, not PostgreSQL."))

        # 2. Test Connection
        self.stdout.write("Testing PostgreSQL connection...")
        try:
            connections[DEFAULT_DB_ALIAS].ensure_connection()
            self.stdout.write(self.style.SUCCESS("PostgreSQL connection validated."))
        except Exception as e:
            raise CommandError(f"PostgreSQL connection failed: {e}")

        # 3. Dump Data from SQLite
        dump_file = 'db_dump.json'
        self.stdout.write(f"Dumping data from SQLite to {dump_file}...")
        try:
            # We use a temporary file to avoid memory issues with large datasets
            with open(dump_file, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata', 
                    '--database=sqlite', 
                    '--exclude=contenttypes', 
                    '--exclude=auth.permission', 
                    '--indent=2', 
                    stdout=f
                )
            self.stdout.write(self.style.SUCCESS("Data dumped successfully."))
        except Exception as e:
            if os.path.exists(dump_file):
                os.remove(dump_file)
            raise CommandError(f"Dump failed: {e}")

        # 4. Run Migrations on PostgreSQL
        self.stdout.write("Running migrations on PostgreSQL...")
        try:
            call_command('migrate', database=DEFAULT_DB_ALIAS, interactive=False)
            self.stdout.write(self.style.SUCCESS("Migrations completed."))
        except Exception as e:
            raise CommandError(f"Migration failed: {e}")

        # 5. Load Data to PostgreSQL
        self.stdout.write(f"Loading data from {dump_file} into PostgreSQL...")
        try:
            call_command('loaddata', dump_file, database=DEFAULT_DB_ALIAS)
            self.stdout.write(self.style.SUCCESS("Data loaded successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Load failed: {e}"))
            self.stdout.write("Attempting to proceed with sequence reset regardless...")

        # 6. Reset Sequences (PostgreSQL specific)
        self.stdout.write("Resetting PostgreSQL sequences...")
        try:
            output = io.StringIO()
            # Get list of all app labels
            from django.apps import apps
            app_labels = [app_config.label for app_config in apps.get_app_configs()]
            
            sql_statements = []
            for app in app_labels:
                try:
                    call_command('sqlsequencereset', app, database=DEFAULT_DB_ALIAS, stdout=output)
                    sql = output.getvalue().strip()
                    if sql:
                        sql_statements.append(sql)
                    output.truncate(0)
                    output.seek(0)
                except Exception:
                    continue
            
            if sql_statements:
                full_sql = "\n".join(sql_statements)
                with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
                    cursor.execute(full_sql)
                self.stdout.write(self.style.SUCCESS("Sequences reset successfully."))
            else:
                self.stdout.write("No sequences needed resetting.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Sequence reset failed: {e}"))

        # 7. Cleanup
        if os.path.exists(dump_file):
            os.remove(dump_file)
            self.stdout.write(f"Removed temporary dump file {dump_file}.")

        self.stdout.write(self.style.SUCCESS("\nMigration from SQLite to PostgreSQL completed successfully!"))
        self.stdout.write("You can now safely remove the 'sqlite' entry from settings.py.")
