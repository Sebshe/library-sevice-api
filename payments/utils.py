import stripe
from _decimal import Decimal
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from payments.models import Payment
from payments.stipe_utils import create_stripe_session

stripe.api_key = settings.STRIPE_SECRET_KEY

FINE_MULTIPLIER = 2


def create_payment_and_stripe_session(
    borrowing, success_url, cancel_url, payment_type
) -> Payment:
    if payment_type == "PAYMENT":
        days_borrowed = borrowing.extend_return_date - borrowing.borrow_date
        money_to_pay = Decimal(days_borrowed.days) * borrowing.book.daily_fee
        payment_type = Payment.PaymentType.PAYMENT

    elif payment_type == "FINE":
        days_overdue = (
            borrowing.actual_return_date - borrowing.expected_return_date
        ).days
        money_to_pay = (
            Decimal(days_overdue) * borrowing.book.daily_fee * FINE_MULTIPLIER
        )
        payment_type = Payment.PaymentType.FINE
    else:
        return Response(
            {"error": "Payment type has to be either PAYMENT or FINE"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session = create_stripe_session(
        payment_type, money_to_pay, borrowing.book.title, success_url, cancel_url
    )

    payment = Payment.objects.create(
        borrowing=borrowing,
        stripe_session_url=session["url"],
        stripe_session_id=session["id"],
        status=Payment.PaymentStatus.PENDING,
        type=payment_type,
    )

    return payment
