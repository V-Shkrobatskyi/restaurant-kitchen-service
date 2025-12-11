from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views import generic, View
from django.contrib import messages
from decimal import Decimal

from kitchen.forms import CookCreationForm, CookExperienceUpdateForm, DishForm, CookSearchForm, DishSearchForm, \
    DishTypeSearchForm, RestaurantTableForm
from kitchen.models import DishType, Dish, Cook, RestaurantTable, Order, OrderItem


@login_required
def index(request: HttpRequest) -> HttpResponse:
    num_dishes = Dish.objects.count()
    num_cooks = Cook.objects.count()
    num_dish_types = DishType.objects.count()
    num_visits = request.session.get("num_visits", 0)
    request.session["num_visits"] = num_visits + 1
    context = {
        "num_dishes": num_dishes,
        "num_cooks": num_cooks,
        "num_dish_types": num_dish_types,
        "num_visits": num_visits + 1,
    }
    return render(request, "kitchen/index.html", context)


def get_cart_with_total(request, uuid):
    cart = get_cart(request, uuid).copy()
    items = cart.get("items", [])

    if not items:
        cart["total_price"] = 0
        cart["quantity_map"] = {}
        return cart

    dish_ids = [item["dish_id"] for item in items]

    dishes = Dish.objects.filter(id__in=dish_ids).values('id', 'price')
    price_map = {d['id']: d['price'] for d in dishes}

    total = 0
    quantity_map = {}

    for item in items:
        price = price_map.get(item["dish_id"], 0)
        total += price * item["quantity"]
        quantity_map[item["dish_id"]] = item["quantity"]

    cart["total_price"] = total
    cart["quantity_map"] = quantity_map
    return cart


def get_cart_key(uuid):
    return f"cart_{uuid}"


def get_cart(request, uuid):
    key = get_cart_key(uuid)
    return request.session.get(key, {"items": []})


def save_cart(request, uuid, cart):
    key = get_cart_key(uuid)
    request.session[key] = cart
    request.session.modified = True


def clear_cart(request, uuid):
    key = get_cart_key(uuid)
    if key in request.session:
        del request.session[key]
        request.session.modified = True


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


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


class RestaurantTableListView(LoginRequiredMixin, View):
    template_name = "kitchen/restauranttable_list.html"

    def get(self, request):
        if not request.user.is_staff:
            return redirect("/")

        tables = RestaurantTable.objects.all().order_by("number")

        # Add active orders
        tables_data = []
        for t in tables:
            orders = t.orders.filter(
                status__in=["new", "accepted", "preparing", "served"]
            ).order_by("-created_at")
            tables_data.append((t, orders))

        return render(request, self.template_name, {
            "tables": tables,
            "tables_data": tables_data
        })


class RestaurantTableCreateView(LoginRequiredMixin, generic.CreateView):
    model = RestaurantTable
    form_class = RestaurantTableForm
    template_name = "kitchen/restauranttable_form.html"
    success_url = reverse_lazy("kitchen:table-list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("/")  # block non-staff users
        return super().dispatch(request, *args, **kwargs)


class TableLandingView(View):
    template_name = "kitchen/table_landing.html"

    def get(self, request, uuid):
        table = get_object_or_404(RestaurantTable, uuid=uuid)

        active_statuses = ["new", "accepted", "preparing", "served"]

        if request.user.is_authenticated and request.user.is_staff:
            # STAFF mode
            active_orders = table.orders.filter(status__in=active_statuses).order_by("-created_at")
            return render(request, self.template_name, {
                "table": table,
                "active_orders": active_orders,
                "is_staff": True,
            })

        # GUEST mode
        session_key = f"guest_orders_{uuid}"
        guest_order_ids = request.session.get(session_key, [])

        guest_orders = (
            Order.objects.filter(id__in=guest_order_ids)
            .order_by("-created_at")
        )

        return render(request, self.template_name, {
            "table": table,
            "guest_orders": guest_orders,
            "is_staff": False,
        })


class TableMenuView(View):
    template_name = "kitchen/table_menu.html"
    fragment_template_name = "kitchen/partials/dishes_grid_fragment.html"
    cart_fragment_name = "kitchen/partials/cart_button_fragment.html"

    def get(self, request, uuid):
        table = get_object_or_404(RestaurantTable, uuid=uuid)
        dish_types = DishType.objects.all().order_by("name")
        selected_type = request.GET.get("type")

        if selected_type:
            dishes = Dish.objects.filter(dish_type_id=selected_type).order_by("name")
        else:
            dishes = Dish.objects.all().order_by("name")

        cart = get_cart_with_total(request, uuid)

        context = {
            "table": table,
            "dishes": dishes,
            "dish_types": dish_types,
            "selected_type": selected_type,
            "cart": cart,
        }

        if 'HX-Request' in request.headers:
            return render(request, "kitchen/partials/dishes_grid_fragment.html", context)

        return render(request, self.template_name, context)


class UpdateCartView(View):
    def post(self, request, uuid, dish_id, action):
        table = get_object_or_404(RestaurantTable, uuid=uuid)
        dish = get_object_or_404(Dish, id=dish_id)
        cart = get_cart(request, uuid)

        found_item = next((item for item in cart["items"] if item["dish_id"] == dish.id), None)

        if action == 'add':
            if found_item:
                found_item["quantity"] += 1
            else:
                cart["items"].append({"dish_id": dish.id, "quantity": 1})

        elif action == 'decrease' and found_item:
            if found_item["quantity"] > 1:
                found_item["quantity"] -= 1
            else:
                cart["items"].remove(found_item)

        save_cart(request, uuid, cart)

        if 'HX-Request' in request.headers:
            cart_for_display = get_cart_with_total(request, uuid)

            context = {
                "table": table,
                "cart": cart_for_display,
                "dish": dish,
            }

            dish_form_html = render_to_string(
                'kitchen/partials/dish_form_fragment.html',
                context, request=request
            )

            cart_context = context.copy()
            cart_context['is_oob'] = True
            cart_btn_html = render_to_string(
                'kitchen/partials/cart_button_fragment.html',
                cart_context, request=request
            )

            return HttpResponse(dish_form_html + cart_btn_html)

        return redirect(request.META.get("HTTP_REFERER", f"/table/{uuid}/menu/"))


class RemoveFromCartView(View):
    def post(self, request, uuid, dish_id):
        cart = get_cart(request, uuid)

        cart["items"] = [
            item for item in cart["items"]
            if item["dish_id"] != dish_id
        ]

        save_cart(request, uuid, cart)
        return redirect("kitchen:table-cart", uuid=uuid)


class CartView(View):
    template_name = "kitchen/cart.html"

    def get(self, request, uuid):
        table = get_object_or_404(RestaurantTable, uuid=uuid)
        cart = get_cart(request, uuid)

        detailed_items = []
        total = Decimal("0.00")

        for item in cart["items"]:
            dish = Dish.objects.get(id=item["dish_id"])
            subtotal = dish.price * item["quantity"]
            detailed_items.append({
                "dish": dish,
                "quantity": item["quantity"],
                "subtotal": subtotal,
            })
            total += subtotal

        return render(request, self.template_name, {
            "table": table,
            "items": detailed_items,
            "total": total,
        })


class CheckoutView(View):
    def post(self, request, uuid):
        table = get_object_or_404(RestaurantTable, uuid=uuid)
        cart = get_cart(request, uuid)

        if not cart["items"]:
            messages.error(request, "The cart is empty.")
            return redirect("kitchen:table-cart", uuid=uuid)

        order = Order.objects.create(
            table=table,
            user=request.user if request.user.is_authenticated else None,
            status="new",
        )

        for item in cart["items"]:
            dish = Dish.objects.get(id=item["dish_id"])
            OrderItem.objects.create(
                order=order,
                dish=dish,
                quantity=item["quantity"],
                price=dish.price,
            )

        # save guest order history
        if not request.user.is_authenticated:
            key = f"guest_orders_{uuid}"
            prev = request.session.get(key, [])
            prev.append(order.id)
            request.session[key] = prev
            request.session.modified = True
            print("GUEST SESSION AFTER CHECKOUT:", request.session.get(key))

        clear_cart(request, uuid)

        messages.success(request, "The order has been successfully created!")
        return redirect("kitchen:table-landing", uuid=uuid)
