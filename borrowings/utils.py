from datetime import date
from typing import Optional
from django.db import transaction
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing
from users.models import User


def check_book_availability(book: Book) -> Optional[dict]:
    if book.inventory <= 0:
        return {"message": "Book is out of stock"}
    return None


def create_borrowing(user: User, book: Book, extend_return_date: date) -> Response:
    availability_response = check_book_availability(book)
    if availability_response:
        return Response(availability_response, status=400)

    with transaction.atomic():
        borrowing = Borrowing.objects.create(
            extend_return_date=extend_return_date, user=user, book=book
        )
        book.inventory -= 1
        book.save()

    return borrowing
