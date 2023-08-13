from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing
from borrowings.utils import create_borrowing

User = get_user_model()


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request")
        book_id = request.data.get("book_id")
        extend_return_date = request.data.get("extend_return_date")
        book = get_object_or_404(Book, id=book_id)

        borrowing = create_borrowing(request.user, book, extend_return_date)

        return borrowing


class BorrowingDetailSerializer(serializers.ModelSerializer):
    user = serializers.EmailField(source="user.email", read_only=True)
    book = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Borrowing
        fields = "__all__"
