from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from kitchen.models import DishType, Dish, Cook, Table, Order, OrderItem


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "dish_type", "likes"]
    list_filter = ["dish_type",]
    search_fields = ["name", ]


@admin.register(Cook)
class CookAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("years_of_experience", )
    fieldsets = UserAdmin.fieldsets + (
        ("Additional info", {"fields": ("years_of_experience",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional info", {"fields": ("first_name", "last_name", "years_of_experience",)}),
    )


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["number", "uuid", "description"]
    search_fields = ["number", "description"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "table", "status", "created_at", "get_total"]
    list_filter = ["status", "table"]
    inlines = [OrderItemInline]


admin.site.register(DishType)
