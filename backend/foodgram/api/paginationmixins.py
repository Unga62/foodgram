from rest_framework import viewsets

from api.pagination import CustomPagination


class PaginationMixins(viewsets.GenericViewSet):
    pagination_class = CustomPagination
