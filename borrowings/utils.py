from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import serializers
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing


def create_borrowing(book_id, extend_return_date, user):
    book = get_object_or_404(Book, id=book_id)

    if book.inventory > 0:
        with transaction.atomic():
            borrowing = Borrowing.objects.create(
                extend_return_date=extend_return_date, user=user, book=book
            )
            book.inventory -= 1
            book.save()
            return borrowing
    else:
        raise serializers.ValidationError({"message": "Book is out of stock"})
