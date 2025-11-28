from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from kitchen.models import DishType, Dish, Cook, RestaurantTable, Order, OrderItem


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "dish_type"]
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


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    fields = ("number",)
    readonly_fields = ("qr_code",)  # QR code generate automatically


admin.site.register(DishType)
admin.site.register(Order)
admin.site.register(OrderItem)
