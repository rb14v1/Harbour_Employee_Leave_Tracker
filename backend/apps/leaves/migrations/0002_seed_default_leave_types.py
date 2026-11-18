from django.db import migrations

DEFAULT_LEAVE_TYPES = [
    ("Casual Leave", 12),
    ("Sick Leave", 10),
    ("Earned Leave", 15),
    ("Unpaid Leave", None),
]


def seed_leave_types(apps, schema_editor):
    LeaveType = apps.get_model("leaves", "LeaveType")
    for name, allowance in DEFAULT_LEAVE_TYPES:
        LeaveType.objects.update_or_create(name=name, defaults={"default_annual_allowance": allowance})


def unseed_leave_types(apps, schema_editor):
    LeaveType = apps.get_model("leaves", "LeaveType")
    LeaveType.objects.filter(name__in=[name for name, _ in DEFAULT_LEAVE_TYPES], applications__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("leaves", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_leave_types, unseed_leave_types),
    ]
