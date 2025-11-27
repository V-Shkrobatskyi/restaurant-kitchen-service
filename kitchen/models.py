import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class DishType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name", )

    def __str__(self):
        return self.name


class Cook(AbstractUser):
    years_of_experience = models.PositiveSmallIntegerField(
        default=0,
    )

    class Meta:
        ordering = ("username", )

    def __str__(self):
        return f"{self.username}: ({self.first_name} {self.last_name})"

    def get_absolute_url(self):
        return reverse("kitchen:cook-detail", kwargs={"pk": self.pk})


class Dish(models.Model):
    name = models.CharField(max_length=127, unique=True)
    description = models.TextField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    likes = models.PositiveIntegerField(default=0)
    # Many-to-One
    dish_type = models.ForeignKey(
        DishType,
        on_delete=models.CASCADE,
        related_name="dishes"
    )
    # Many-to-many
    cooks = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="dishes")

    class Meta:
        ordering = ("name", )

    def __str__(self):
        return f"{self.name} (price: {self.price}, dish_type: {self.dish_type.name})"


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("number", )

    def __str__(self):
        return f"Table {self.number}"

    def get_absolute_url(self):
        return reverse("kitchen:table-detail", kwargs={"pk": self.pk})


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at", )

    def __str__(self):
        return f"Order #{self.id} - {self.table}"

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("id", )

    def __str__(self):
        return f"{self.quantity}x {self.dish.name}"

    def get_subtotal(self):
        return self.dish.price * self.quantity
