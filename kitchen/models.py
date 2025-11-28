from django.contrib.auth.models import AbstractUser
import io
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
import qrcode


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


class RestaurantTable(models.Model):
    number = models.PositiveIntegerField(unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code = models.ImageField(upload_to='table_qr/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('number',)

    def __str__(self):
        return f"Table {self.number} ({self.uuid})"

    def get_absolute_url(self):
        return reverse('kitchen:table-order', kwargs={'uuid': str(self.uuid)})

    def save(self, *args, **kwargs):
        # Ensure uuid exists before generating QR
        if not self.uuid:
            self.uuid = uuid.uuid4()
        # Generate QR only if missing
        if not self.qr_code:
            path = self.get_absolute_url()
            site = getattr(settings, 'SITE_URL', '')
            full_url = site.rstrip('/') + path
            img = qrcode.make(full_url)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            name = f'table_{self.uuid}.png'
            self.qr_code.save(name, ContentFile(buf.read()), save=False)
            buf.close()
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('served', 'Served'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    table = models.ForeignKey('RestaurantTable', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"

    @property
    def total(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.total_price
        return total


class OrderItem(models.Model):
    order = models.ForeignKey('Order', related_name='items', on_delete=models.CASCADE)
    dish = models.ForeignKey('kitchen.Dish', on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)
    price = models.DecimalField(max_digits=7, decimal_places=2, help_text='Price at time of order')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return f"{self.quantity} x {self.dish.name}"

    def save(self, *args, **kwargs):
        # set price from Dish if not provided
        if not self.price:
            self.price = self.dish.price
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        return (self.price or Decimal('0.00')) * self.quantity
