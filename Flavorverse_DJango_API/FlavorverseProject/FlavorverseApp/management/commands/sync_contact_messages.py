from django.core.management.base import BaseCommand
from FlavorverseApp.models import ContactMessage

class Command(BaseCommand):
    help = "Sync contact messages from Flask API to Django database"
    
    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.NOTICE("Starting sync of contact messages from Flask API..."))
            
            success = ContactMessage.sync_from_flask()
            
            if success:
                count = ContactMessage.objects.count()
                self.stdout.write(self.style.SUCCESS(f"Successfully synced contact messages. Total messages: {count}"))
            else:
                self.stdout.write(self.style.ERROR("Failed to sync contact messages from Flask API."))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}")) 