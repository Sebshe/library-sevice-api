from datetime import date

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingDetailSerializer
from borrowings.tasks import send_telegram_message
from library_service_api import settings
from payments.utils import create_payment_and_stripe_session

SUCCESS_URL = (
    f"{settings.DOMAIN_URL}/payments/success?session_id={{CHECKOUT_SESSION_ID}}"
)
CANCEL_URL = f"{settings.DOMAIN_URL}/payments/cancel?session_id={{CHECKOUT_SESSION_ID}}"


class BorrowingViewSet(viewsets.ModelViewSet):
    """
    Define the Borrowing ViewSet
    """

    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)

    def check_book_availability(self, book):
        if book.inventory <= 0:
            return Response({"message": "Book is out of stock"}, status=status.HTTP_400_BAD_REQUEST)
        return None

    def create(self, request, *args, **kwargs):
        book_id = request.data.get("book_id")
        extend_return_date = request.data.get("extend_return_date")
        book = get_object_or_404(Book, id=book_id)

        availability_response = self.check_book_availability(book)
        if availability_response:
            return availability_response

        with transaction.atomic():
            borrowing = Borrowing.objects.create(
                extend_return_date=extend_return_date, user=request.user, book=book
            )
            book.inventory -= 1
            book.save()
            serializer = self.get_serializer(borrowing)
            message = f"New borrowing created: {borrowing.book.title} by {borrowing.user.email}"
            send_telegram_message.delay(message)
            return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        """
        Custom action to handle returning a borrowed book
        """
        borrowing = Borrowing.objects.get(id=pk)
        if borrowing.user != self.request.user:
            return Response({"message": "It's not your borrowing"}, status=400)
        if borrowing.actual_return_date is None:
            with transaction.atomic():
                borrowing.actual_return_date = date.today()
                borrowing.save()
                borrowing.book.inventory += 1
                borrowing.book.save()

                _payment_type = None
                _message = ""
                if borrowing.actual_return_date > borrowing.extend_return_date:
                    _payment_type = "FINE"
                    _message = "Your borrowing was overdue. You`ll have to pay fine."
                else:
                    _payment_type = "PAYMENT"
                    _message = "Thank you for the timely return of the book"

                payment = create_payment_and_stripe_session(
                    borrowing,
                    success_url=SUCCESS_URL,
                    cancel_url=CANCEL_URL,
                    payment_type=_payment_type,
                )
                send_telegram_message.delay(
                    f"{borrowing.user} successful payment for {borrowing.book}"
                )
                return Response(
                    {
                        "success": "The book was successfully returned.",
                        "message": _message,
                        "link": f"Pay here: {payment.stripe_session_url}",
                    },
                    status=status.HTTP_200_OK,
                )
        return Response({"message": "Borrowing already returned"}, status=400)

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.GET.get("user_id")
        is_active = self.request.GET.get("is_active")

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            if is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BorrowingDetailSerializer(instance)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_active",
                type=OpenApiTypes.BOOL,
                description="Filter if books already returned or not (ex. ?is_active=True)",
            ),
            OpenApiParameter(
                "user_id",
                type=OpenApiTypes.INT,
                description="If user is admin he can filter by user id (ex. ?user_id=1)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(self, request, *args, **kwargs)
