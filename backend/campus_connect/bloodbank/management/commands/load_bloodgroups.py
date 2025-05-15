from django.core.management.base import BaseCommand
from bloodbank.models import BloodGroup

class Command(BaseCommand):
    help = 'Load common blood groups into the database'

    BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']

    def handle(self, *args, **kwargs):
        created_count = 0
        for name in self.BLOOD_GROUPS:
            obj, created = BloodGroup.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created blood group: {name}'))
                created_count += 1
            else:
                self.stdout.write(f'Blood group already exists: {name}')
        self.stdout.write(self.style.SUCCESS(f'Total blood groups created: {created_count}'))
