from django.contrib import admin
from .models import Department, SchoolMaster


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'secretary', 'chief')


class SchoolMasterAdmin(admin.ModelAdmin):
    list_display = ('staff', 'duty', 'dutyDiscript')

# Register your models here.
admin.site.register(Department, DepartmentAdmin)
admin.site.register(SchoolMaster, SchoolMasterAdmin)
