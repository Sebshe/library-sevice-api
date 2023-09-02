from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.utils import create_borrowing

User = get_user_model()


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = "__all__"

    def create(self, request, *args, **kwargs):
        book_id = request.data.get("book_id")
        extend_return_date = request.data.get("extend_return_date")
        borrowing = create_borrowing(book_id, extend_return_date, request.user)
        serializer = self.get_serializer(borrowing)
        return Response(serializer.data)


class BorrowingDetailSerializer(serializers.ModelSerializer):
    user = serializers.EmailField(source="user.email", read_only=True)
    book = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Borrowing
        fields = "__all__"
