from django.contrib import admin
from .models import (
    Color,
    DefectType,
    QualityQcFa,
    InspectionDefect,
    SecondsA4,
    SecondsGeneral,
    ContainerDefectType,
    Container,
    ContainerInspectionDefect,
)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


class InspectionDefectInline(admin.TabularInline):
    model = InspectionDefect
    extra = 1


@admin.register(QualityQcFa)
class QualityQcFaAdmin(admin.ModelAdmin):
    list_display = ('table_type', 'date_1', 'customer', 'style', 'color', 'pass_or_fail')
    list_filter = ('table_type', 'pass_or_fail', 'color')
    search_fields = ('customer', 'style', 'po')
    inlines = [InspectionDefectInline]


@admin.register(InspectionDefect)
class InspectionDefectAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'defect_type', 'amount')
    list_filter = ('defect_type',)
    search_fields = ('inspection__customer', 'defect_type__name')


@admin.register(SecondsA4)
class SecondsA4Admin(admin.ModelAdmin):
    list_display = ('year', 'week', 'style', 'color', 'line', 'percentage_of_2ds')
    list_filter = ('year', 'week', 'line', 'color')
    search_fields = ('style', 'line')


@admin.register(SecondsGeneral)
class SecondsGeneralAdmin(admin.ModelAdmin):
    list_display = ('date', 'week', 'customer', 'style')
    list_filter = ('week',)
    search_fields = ('date',)


@admin.register(ContainerDefectType)
class ContainerDefectTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


class ContainerInspectionDefectInline(admin.TabularInline):
    model = ContainerInspectionDefect
    extra = 1


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ('container_number', 'customer', 'percentage_pass', 'percentage_reject')
    list_filter = ('customer',)
    search_fields = ('container_number', 'customer')
    inlines = [ContainerInspectionDefectInline]


@admin.register(ContainerInspectionDefect)
class ContainerInspectionDefectAdmin(admin.ModelAdmin):
    list_display = ('container', 'defect_type', 'amount')
    list_filter = ('defect_type',)
    search_fields = ('container__customer', 'defect_type__name')
