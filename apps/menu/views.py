from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import MenuItem

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

    def get_template_names(self):
        """Return different template based on item type"""
        if self.kwargs.get('item_type') == 'extra' or self.extra_context and self.extra_context.get('item_type') == 'extra':
            return ["menu/extra_list.html"]
        return ["menu/item_list.html"]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by item type
        item_type = self.kwargs.get('item_type') or (self.extra_context and self.extra_context.get('item_type'))
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        
        # Availability filter
        availability = self.request.GET.get("availability")
        if availability:
            queryset = queryset.filter(is_available=(availability == "available"))
        
        # Search functionality
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
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
            "total_items": self.get_queryset().count(),
            "item_type": self.kwargs.get('item_type') or (self.extra_context and self.extra_context.get('item_type', 'regular'))
        })
        return context
