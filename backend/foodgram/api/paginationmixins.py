from api.pagination import CustomPagination
from rest_framework import viewsets


class PaginationMixins(viewsets.GenericViewSet):
    pagination_class = CustomPagination
