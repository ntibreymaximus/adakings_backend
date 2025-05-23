from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from .models import MenuItem, Extra

def is_admin_staff(user):
    return user.is_authenticated and user.is_staff and getattr(user, "role", None) == "admin"

class StaffViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class MenuItemListView(StaffViewMixin, ListView):
    model = MenuItem
    template_name = "menu/item_list.html"
    context_object_name = "items"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related("available_extras")
        
        # Availability filter
        availability = self.request.GET.get("availability")
        if availability:
            queryset = queryset.filter(is_available=(availability == "available"))
        
        # Search functionality
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Sorting
        sort_by = self.request.GET.get("sort", "name")
        if sort_by == "price":
            queryset = queryset.order_by("price")
        elif sort_by == "price-desc":
            queryset = queryset.order_by("-price")
        else:
            queryset = queryset.order_by("name")

        return queryset.select_related("created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "is_admin": is_admin_staff(self.request.user),
            "selected_availability": self.request.GET.get("availability"),
            "search_query": self.request.GET.get("search"),
            "sort_by": self.request.GET.get("sort", "name"),
            "total_items": self.get_queryset().count()
        })
        return context

class ExtraListView(StaffViewMixin, ListView):
    model = Extra
    template_name = "menu/extra_list.html"
    context_object_name = "extras"
    paginate_by = 20

    def get_queryset(self):
        queryset = Extra.objects.annotate(
            menu_items_count=Count("menu_items")
        ).prefetch_related("menu_items")
        
        # Availability filter
        availability = self.request.GET.get("availability")
        if availability:
            queryset = queryset.filter(is_available=(availability == "available"))
        
        # Search functionality
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Sorting
        sort_by = self.request.GET.get("sort", "name")
        if sort_by == "price":
            queryset = queryset.order_by("price")
        elif sort_by == "price-desc":
            queryset = queryset.order_by("-price")
        else:
            queryset = queryset.order_by("name")
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "is_admin": is_admin_staff(self.request.user),
            "selected_availability": self.request.GET.get("availability"),
            "search_query": self.request.GET.get("search"),
            "sort_by": self.request.GET.get("sort", "name"),
            "total_extras": self.get_queryset().count()
        })
        return context
