import base64
from io import BytesIO

import qrcode
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import generic, View
from django.views.decorators.http import require_POST

from kitchen.forms import (
    CookCreationForm,
    CookExperienceUpdateForm,
    DishForm,
    CookSearchForm,
    DishSearchForm,
    DishTypeSearchForm,
    TableForm,
    TableSearchForm,
)
from kitchen.models import DishType, Dish, Cook, Table, Order, OrderItem


@login_required
def index(request: HttpRequest) -> HttpResponse:
    num_dishes = Dish.objects.count()
    num_cooks = Cook.objects.count()
    num_dish_types = DishType.objects.count()
    num_tables = Table.objects.count()
    num_orders = Order.objects.filter(status="pending").count()
    num_visits = request.session.get("num_visits", 0)
    request.session["num_visits"] = num_visits + 1
    context = {
        "num_dishes": num_dishes,
        "num_cooks": num_cooks,
        "num_dish_types": num_dish_types,
        "num_tables": num_tables,
        "num_orders": num_orders,
        "num_visits": num_visits + 1,
    }
    return render(request, "kitchen/index.html", context)


class DishTypeListView(LoginRequiredMixin, generic.ListView):
    model = DishType
    template_name = "kitchen/dish_type_list.html"
    context_object_name = "dish_type_list"
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DishTypeListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = DishTypeSearchForm(
            initial={"name": name}
        )
        return context

    def get_queryset(self):
        queryset = DishType.objects.all()
        form = DishTypeSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(name__icontains=form.cleaned_data["name"])
        return queryset


class DishTypeCreateView(LoginRequiredMixin, generic.CreateView):
    model = DishType
    fields = "__all__"
    success_url = reverse_lazy("kitchen:dish-type-list")
    template_name = "kitchen/dish_type_form.html"

    def get_template_names(self):
        # HTMX: return only the create form partial
        if self.request.headers.get("HX-Request") == "true":
            return ["kitchen/partials/dish_type_form_create_partial.html"]
        # Normal request: full page with layout
        return [self.template_name]

    def form_valid(self, form):
        self.object = form.save()

        # HTMX: return a single new table row to append to the list
        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request,
                "kitchen/partials/dish_type_row.html",
                {"dish_type": self.object},
            )

        # Non-HTMX: standard redirect
        return HttpResponseRedirect(self.get_success_url())


class DishTypeUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = DishType
    fields = "__all__"
    success_url = reverse_lazy("kitchen:dish-type-list")
    template_name = "kitchen/dish_type_form.html"

    def get_template_names(self):
        # If this is an HTMX request – return only the partial template
        if self.request.headers.get("HX-Request") == "true":
            return ["kitchen/partials/dish_type_form_partial.html"]
        # Otherwise – return the full template as usual
        return [self.template_name]

    def form_valid(self, form):
        self.object = form.save()

        if self.request.headers.get("HX-Request") == "true":
            # Return just the updated table row
            return render(
                self.request,
                "kitchen/partials/dish_type_row.html",
                {"dish_type": self.object},
            )

        # Fallback for normal requests
        return HttpResponseRedirect(self.get_success_url())


class DishTypeDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = DishType
    success_url = reverse_lazy("kitchen:dish-type-list")
    template_name = "kitchen/dish_type_confirm_delete.html"

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return ["kitchen/partials/dish_type_confirm_delete_partial.html"]
        return [self.template_name]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.headers.get("HX-Request") == "true":
            # empty response → <tr> will be removed
            return HttpResponse("")

        return HttpResponseRedirect(self.get_success_url())


class CookListView(LoginRequiredMixin, generic.ListView):
    model = Cook
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CookListView, self).get_context_data(**kwargs)
        username = self.request.GET.get("username", "")
        context["search_form"] = CookSearchForm(
            initial={"username": username}
        )
        return context

    def get_queryset(self):
        queryset = Cook.objects.all()
        form = CookSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                username__icontains=form.cleaned_data["username"]
            )
        return queryset


class CookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Cook


class CookCreateView(LoginRequiredMixin, generic.CreateView):
    model = Cook
    form_class = CookCreationForm


class CookExperienceUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Cook
    form_class = CookExperienceUpdateForm
    success_url = reverse_lazy("kitchen:cook-list")


class CookDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Cook
    success_url = reverse_lazy("kitchen:cook-list")


class DishListView(LoginRequiredMixin, generic.ListView):
    model = Dish
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DishListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = DishSearchForm(
            initial={"name": name}
        )
        return context

    def get_queryset(self):
        queryset = Dish.objects.all().select_related("dish_type")
        form = DishSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(name__icontains=form.cleaned_data["name"])
        return queryset


class DishDetailView(LoginRequiredMixin, generic.DetailView):
    model = Dish


class DishCreateView(LoginRequiredMixin, generic.CreateView):
    model = Dish
    form_class = DishForm
    success_url = reverse_lazy("kitchen:dish-list")


class DishUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Dish
    form_class = DishForm
    success_url = reverse_lazy("kitchen:dish-list")


class DishDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Dish
    success_url = reverse_lazy("kitchen:dish-list")


class DishAssignView(LoginRequiredMixin, View):
    model = Dish

    def post(self, request, pk):
        user = get_user(request)
        cooks = Dish.objects.get(id=pk).cooks
        if user in cooks.all():
            cooks.remove(user)
        else:
            cooks.add(user)
        return HttpResponseRedirect(reverse("kitchen:dish-detail", args=[pk]))


# Table views (for authenticated staff)
class TableListView(LoginRequiredMixin, generic.ListView):
    model = Table
    template_name = "kitchen/table_list.html"
    context_object_name = "table_list"
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(TableListView, self).get_context_data(**kwargs)
        number = self.request.GET.get("number", "")
        context["search_form"] = TableSearchForm(
            initial={"number": number}
        )
        return context

    def get_queryset(self):
        queryset = Table.objects.all()
        form = TableSearchForm(self.request.GET)
        if form.is_valid():
            number = form.cleaned_data.get("number")
            if number:
                queryset = queryset.filter(number=number)
        return queryset


class TableDetailView(LoginRequiredMixin, generic.DetailView):
    model = Table
    template_name = "kitchen/table_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = self.get_object()
        # Generate QR code
        qr_url = self.request.build_absolute_uri(
            reverse("kitchen:public-menu", kwargs={"table_uuid": table.uuid})
        )
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        context["qr_code"] = qr_code_base64
        context["qr_url"] = qr_url
        context["recent_orders"] = table.orders.all()[:5]
        return context


class TableCreateView(LoginRequiredMixin, generic.CreateView):
    model = Table
    form_class = TableForm
    template_name = "kitchen/table_form.html"
    success_url = reverse_lazy("kitchen:table-list")


class TableUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Table
    form_class = TableForm
    template_name = "kitchen/table_form.html"
    success_url = reverse_lazy("kitchen:table-list")


class TableDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Table
    template_name = "kitchen/table_confirm_delete.html"
    success_url = reverse_lazy("kitchen:table-list")


# Order views (for authenticated staff)
class OrderListView(LoginRequiredMixin, generic.ListView):
    model = Order
    template_name = "kitchen/order_list.html"
    context_object_name = "order_list"
    paginate_by = 10

    def get_queryset(self):
        queryset = Order.objects.all().select_related("table").prefetch_related("items__dish")
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Order.STATUS_CHOICES
        context["current_status"] = self.request.GET.get("status", "")
        return context


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Order
    template_name = "kitchen/order_detail.html"


class OrderUpdateStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get("status")
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
        return HttpResponseRedirect(reverse("kitchen:order-detail", args=[pk]))


# Public views (for customers via QR code)
def public_menu(request, table_uuid):
    """Public menu page for customers to order from a specific table."""
    table = get_object_or_404(Table, uuid=table_uuid)
    dishes = Dish.objects.all().select_related("dish_type").order_by("dish_type__name", "name")
    dish_types = DishType.objects.all()

    # Get or create cart from session
    cart_key = f"cart_{table_uuid}"
    cart = request.session.get(cart_key, {})

    # Calculate cart total
    cart_items = []
    cart_total = 0
    for dish_id, quantity in cart.items():
        try:
            dish = Dish.objects.get(id=dish_id)
            subtotal = dish.price * quantity
            cart_items.append({
                "dish": dish,
                "quantity": quantity,
                "subtotal": subtotal,
            })
            cart_total += subtotal
        except Dish.DoesNotExist:
            pass

    context = {
        "table": table,
        "dishes": dishes,
        "dish_types": dish_types,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "cart_count": sum(cart.values()) if cart else 0,
    }
    return render(request, "kitchen/public_menu.html", context)


def add_to_cart(request, table_uuid):
    """Add a dish to the cart."""
    if request.method == "POST":
        table = get_object_or_404(Table, uuid=table_uuid)
        dish_id = request.POST.get("dish_id")

        if dish_id:
            cart_key = f"cart_{table_uuid}"
            cart = request.session.get(cart_key, {})

            # Add or increment quantity
            if dish_id in cart:
                cart[dish_id] += 1
            else:
                cart[dish_id] = 1

            request.session[cart_key] = cart

    return redirect("kitchen:public-menu", table_uuid=table_uuid)


def remove_from_cart(request, table_uuid):
    """Remove a dish from the cart or decrease its quantity."""
    if request.method == "POST":
        table = get_object_or_404(Table, uuid=table_uuid)
        dish_id = request.POST.get("dish_id")

        if dish_id:
            cart_key = f"cart_{table_uuid}"
            cart = request.session.get(cart_key, {})

            if dish_id in cart:
                cart[dish_id] -= 1
                if cart[dish_id] <= 0:
                    del cart[dish_id]

            request.session[cart_key] = cart

    return redirect("kitchen:public-menu", table_uuid=table_uuid)


def clear_cart(request, table_uuid):
    """Clear the entire cart."""
    if request.method == "POST":
        table = get_object_or_404(Table, uuid=table_uuid)
        cart_key = f"cart_{table_uuid}"
        if cart_key in request.session:
            del request.session[cart_key]

    return redirect("kitchen:public-menu", table_uuid=table_uuid)


def submit_order(request, table_uuid):
    """Submit the cart as an order."""
    if request.method == "POST":
        table = get_object_or_404(Table, uuid=table_uuid)
        cart_key = f"cart_{table_uuid}"
        cart = request.session.get(cart_key, {})

        if cart:
            notes = request.POST.get("notes", "")
            order = Order.objects.create(table=table, notes=notes)

            for dish_id, quantity in cart.items():
                try:
                    dish = Dish.objects.get(id=dish_id)
                    OrderItem.objects.create(order=order, dish=dish, quantity=quantity)
                except Dish.DoesNotExist:
                    pass

            # Clear the cart
            del request.session[cart_key]

            return render(request, "kitchen/order_confirmation.html", {
                "table": table,
                "order": order,
            })

    return redirect("kitchen:public-menu", table_uuid=table_uuid)


def like_dish(request, table_uuid):
    """Like a dish (public endpoint)."""
    if request.method == "POST":
        table = get_object_or_404(Table, uuid=table_uuid)
        dish_id = request.POST.get("dish_id")

        if dish_id:
            # Track liked dishes in session to prevent multiple likes
            liked_key = f"liked_dishes_{table_uuid}"
            liked_dishes = request.session.get(liked_key, [])

            if dish_id not in liked_dishes:
                try:
                    dish = Dish.objects.get(id=dish_id)
                    dish.likes += 1
                    dish.save()
                    liked_dishes.append(dish_id)
                    request.session[liked_key] = liked_dishes
                except Dish.DoesNotExist:
                    pass

    return redirect("kitchen:public-menu", table_uuid=table_uuid)
