from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check if database tables exist'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check core_mentor table
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'core_%';
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write("\nFound tables in database:")
            for table in sorted(tables):
                self.stdout.write(f"- {table}")
                
            # Check if all expected tables exist
            expected_tables = {
                'core_mentor',
                'core_project',
                'core_projectimage',
                'core_resume',
                'core_feedback',
                'core_session'
            }
            
            missing_tables = expected_tables - set(tables)
            if missing_tables:
                self.stdout.write("\nMissing tables:")
                for table in sorted(missing_tables):
                    self.stdout.write(f"- {table}")
            else:
                self.stdout.write("\nAll expected tables exist!")
