import os

from _decimal import Decimal
from django.core.validators import URLValidator
from django.db import models
from rest_framework.exceptions import ValidationError

from borrowings.models import Borrowing
from payments.stipe_utils import create_stripe_session

FINE_MULTIPLIER = 2


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"

    class PaymentType(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(max_length=7, choices=PaymentStatus.choices)
    type = models.CharField(max_length=7, choices=PaymentType.choices)
    borrowing = models.ForeignKey(
        to=Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    stripe_session_url = models.TextField(
        validators=[URLValidator()], null=True, blank=True
    )
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True)

    @property
    def money_to_pay(self) -> Decimal:
        if self.type == "PAYMENT":
            days_borrowed = (
                self.borrowing.extend_return_date - self.borrowing.borrow_date
            ).days
            return Decimal(days_borrowed) * self.borrowing.book.daily_fee
        if self.type == "FINE" and self.borrowing.actual_return_date:
            day_overdue = (
                self.borrowing.actual_return_date - self.borrowing.extend_return_date
            ).days
        return (
            Decimal(day_overdue)
            * self.borrowing.book.daily_fee
            * Decimal(FINE_MULTIPLIER)
        )

    def create_stripe_session(self, success_url, cancel_url):
        money_to_pay = self.money_to_pay
        book_title = self.borrowing.book.title
        session = create_stripe_session(
            self.type, money_to_pay, book_title, success_url, cancel_url
        )

        self.stripe_session_id = session["id"]
        self.stripe_session_url = session["url"]
        self.save()

        return session

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)

        existing_payments = Payment.objects.filter(
            borrowing=self.borrowing, type=self.type
        )

        if self.pk:
            existing_payments = existing_payments.exclude(pk=self.pk)

        if existing_payments.exists():
            raise ValidationError(
                {
                    "type": f"A payment with type '{self.type}' already exists for this borrowing."
                }
            )

    def save(self, *args, **kwargs):
        self.validate_unique()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.status
