from django.urls import path
from kitchen.views import (
    index,
    DishTypeListView,
    DishTypeCreateView,
    DishTypeUpdateView,
    DishTypeDeleteView,
    CookListView,
    CookDetailView,
    CookCreateView,
    CookExperienceUpdateView,
    CookDeleteView,
    DishListView,
    DishDetailView,
    DishCreateView,
    DishUpdateView,
    DishDeleteView,
    DishAssignView, RestaurantTableListView, CartView, TableMenuView, TableLandingView, UpdateCartView,
    RemoveFromCartView, CheckoutView, RestaurantTableCreateView,
)


urlpatterns = [
    path("", index, name="index"),
    path("dish-types/", DishTypeListView.as_view(), name="dish-type-list"),
    path("dish-types/create/", DishTypeCreateView.as_view(), name="dish-type-create"),
    path("dish-types/<int:pk>/update/", DishTypeUpdateView.as_view(), name="dish-type-update"),
    path("dish-types/<int:pk>/delete/", DishTypeDeleteView.as_view(), name="dish-type-delete"),
    path("cooks/", CookListView.as_view(), name="cook-list"),
    path("cooks/<int:pk>/", CookDetailView.as_view(), name="cook-detail"),
    path("cooks/create/", CookCreateView.as_view(), name="cook-create"),
    path("cooks/<int:pk>/update/", CookExperienceUpdateView.as_view(), name="cook-update"),
    path("cooks/<int:pk>/delete/", CookDeleteView.as_view(), name="cook-delete"),
    path("dishes/", DishListView.as_view(), name="dish-list"),
    path("dishes/<int:pk>/", DishDetailView.as_view(), name="dish-detail"),
    path("dishes/create/", DishCreateView.as_view(), name="dish-create"),
    path("dishes/<int:pk>/update/", DishUpdateView.as_view(), name="dish-update"),
    path("dishes/<int:pk>/delete/", DishDeleteView.as_view(), name="dish-delete"),
    path("dishes/<int:pk>/assign/", DishAssignView.as_view(), name="dish-assign"),

    # --- Staff table monitor ---
    path("tables/", RestaurantTableListView.as_view(), name="table-list"),
    path("tables/create/", RestaurantTableCreateView.as_view(), name="table-create"),

    # --- Main table landing (guest + staff) ---
    path("table/<uuid:uuid>/", TableLandingView.as_view(), name="table-landing"),

    # --- Menu page (guest selects dishes) ---
    path("table/<uuid:uuid>/menu/", TableMenuView.as_view(), name="table-menu"),

    # --- Cart page ---
    path("table/<uuid:uuid>/cart/", CartView.as_view(), name="table-cart"),

    # --- Cart modification ---
    path("table/<uuid:uuid>/add/<int:dish_id>/<str:action>/", UpdateCartView.as_view(), name="table-update-cart"),
    path("table/<uuid:uuid>/remove/<int:dish_id>/", RemoveFromCartView.as_view(), name="table-remove-from-cart"),

    # --- Checkout (creates Order + OrderItems) ---
    path("table/<uuid:uuid>/checkout/", CheckoutView.as_view(), name="table-checkout"),
]

app_name = "kitchen"
