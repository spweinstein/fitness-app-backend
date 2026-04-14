from rest_framework.pagination import PageNumberPagination


class CatalogPagination(PageNumberPagination):
    """
    Pagination for catalog list endpoints (templates, plans).
    Only activates when `page` is explicitly present in the request query params.
    Callers that omit `page` receive a plain array (full list), preserving
    backwards compatibility with pickers and other non-paginated consumers.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if "page" not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)
