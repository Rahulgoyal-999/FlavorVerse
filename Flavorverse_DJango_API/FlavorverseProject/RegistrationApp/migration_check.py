"""
Helper utility to check if migrations are needed for social auth fields
"""
from django.core.management import execute_from_command_line
import sys
import os

def check_migrations_needed():
    """Check if migrations are needed for the RegisterUser model"""
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlavorverseProject.settings')
    try:
        # Run the migration check command
        execute_from_command_line(['manage.py', 'makemigrations', '--dry-run'])
        print("Migration check complete. See above for results.")
    except Exception as e:
        print(f"Error checking migrations: {e}")

if __name__ == "__main__":
    check_migrations_needed() 