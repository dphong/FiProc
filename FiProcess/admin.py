from django.contrib import admin
from .models import Department, SchoolMaster, Staff, FiStaffCode
from django import forms
from django.db.models import Q


class DepartmentSelectForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'secretary', 'chief']

    def __init__(self, *args, **kwargs):
        super(DepartmentSelectForm, self).__init__(*args, **kwargs)
        self.fields['secretary'].queryset = Staff.objects.filter(department__id=self.instance.id)
        self.fields['chief'].queryset = Staff.objects.filter(department__id=self.instance.id)


class SchoolMasterForm(forms.ModelForm):
    class Meta:
        model = SchoolMaster
        fields = ['staff', 'duty', 'dutyDescript']

    def __init__(self, *args, **kwargs):
        super(SchoolMasterForm, self).__init__(*args, **kwargs)
        # school = Staff.objects.filter(department__id=4)
        # superViser = Staff.objects.filter(department__id=5)
        self.fields['staff'].queryset = Staff.objects.filter(Q(department__id=4) | Q(department__id=5))


class StaffCodeForm(forms.ModelForm):
    class Meta:
        model = FiStaffCode
        fields = ['department', 'code', 'name']


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'secretary', 'chief')
    form = DepartmentSelectForm


class SchoolMasterAdmin(admin.ModelAdmin):
    list_display = ('staff', 'duty', 'dutyDescript')
    form = SchoolMasterForm


class StaffCodeAdmin(admin.ModelAdmin):
    list_display = ('department', 'code', 'name')
    form = StaffCodeForm

# Register your models here.
admin.site.register(Department, DepartmentAdmin)
admin.site.register(SchoolMaster, SchoolMasterAdmin)
admin.site.register(FiStaffCode, StaffCodeAdmin)
