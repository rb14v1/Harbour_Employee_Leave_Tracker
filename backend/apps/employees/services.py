from django.db import transaction


@transaction.atomic
def deactivate_employee(employee):
    if employee.is_active:
        employee.is_active = False
        employee.save(update_fields=["is_active", "updated_at"])
    return employee
