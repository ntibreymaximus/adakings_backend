from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import MenuItem
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from apps.users.decorators import role_required_class

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
        item_type_filter_value = self.kwargs.get('item_type') or \
                                 (self.extra_context and self.extra_context.get('item_type'))

        # If the view is specifically for 'extra' items, filter by item_type='extra'.
        # Otherwise (e.g. for the main item_list page, where item_type_filter_value might be 'regular' or None),
        # do not filter by item_type, thus including all items (regular and extras).
        if item_type_filter_value == 'extra':
            queryset = queryset.filter(item_type=item_type_filter_value)
        # If item_type_filter_value is 'regular' or None, no item_type filter is applied here.
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

        # Determine if this view is specifically for 'extra' items
        is_extra_specific_view = self.kwargs.get('item_type') == 'extra' or \
                                 (self.extra_context and self.extra_context.get('item_type') == 'extra')

        if not is_extra_specific_view:
            # For the main item_list.html, which shows all items (regular and extras).
            # context[self.context_object_name] (i.e., context['items']) holds the paginated list.
            # Split these items into regular and extras for grouped display in the template.
            items_on_page = context.get(self.context_object_name, []) 
            
            regular_items_on_page = []
            extra_items_on_page = []
            for item in items_on_page:
                if item.item_type == 'regular':
                    regular_items_on_page.append(item)
                elif item.item_type == 'extra':
                    extra_items_on_page.append(item)
            
            context['regular_menu_items'] = regular_items_on_page
            context['extra_menu_items'] = extra_items_on_page
        # If is_extra_specific_view is True, context[self.context_object_name] already contains only 'extra' items,
        # and the extra_list.html template will iterate over it. No special grouping is needed here for that view.

        # --- Standard context variables ---
        is_current_user_frontdesk = False
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'is_frontdesk'):
                is_current_user_frontdesk = self.request.user.is_frontdesk()
            elif hasattr(self.request.user, 'role'):
                is_current_user_frontdesk = (self.request.user.role == 'frontdesk')

        context_updates = {
            "is_admin": is_admin_staff(self.request.user),
            "is_frontdesk": is_current_user_frontdesk,
            "selected_availability": self.request.GET.get("availability"),
            "search_query": self.request.GET.get("search"),
            "sort_by": self.request.GET.get("sort", "name"),
            # total_items should reflect the total count of items matching the query, before pagination
            "total_items": context['paginator'].count if context.get('paginator') else 0,
            # item_type primarily for template display logic (e.g. page title, or identifying the view's purpose)
            "item_type": self.kwargs.get('item_type') or \
                         (self.extra_context and self.extra_context.get('item_type', 'regular'))
        }
        context.update(context_updates)
        return context


@login_required
@role_required_class(allowed_roles=['admin', 'frontdesk'])
@require_POST
def toggle_menu_item_availability(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    item.is_available = not item.is_available
    item.save()
    messages.success(
        request,
        f"Availability of '{item.name}' has been updated to {'Available' if item.is_available else 'Unavailable'}."
    )

    # Determine fallback redirect based on item type
    if item.item_type == 'extra':
        default_redirect_url = 'menu:extra_list'
    else:
        default_redirect_url = 'menu:item_list'
    
    return redirect(request.META.get('HTTP_REFERER', default_redirect_url))
