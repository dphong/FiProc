from django.contrib import admin
from .models import Department, SchoolMaster, Staff
from django import forms


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
        fields = ['staff', 'duty', 'dutyDiscript']

    def __init__(self, *args, **kwargs):
        super(SchoolMasterForm, self).__init__(*args, **kwargs)
        self.fields['staff'].queryset = Staff.objects.filter(department__id=17)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'secretary', 'chief')
    form = DepartmentSelectForm


class SchoolMasterAdmin(admin.ModelAdmin):
    list_display = ('staff', 'duty', 'dutyDiscript')
    form = SchoolMasterForm

# Register your models here.
admin.site.register(Department, DepartmentAdmin)
admin.site.register(SchoolMaster, SchoolMasterAdmin)
