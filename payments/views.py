from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment
from payments.permissions import IsAdminOrSelf
from payments.serializers import PaymentSerializer


class BasePaymentView(APIView):
    """
    Base view for handling payments
    """

    serializer_class = PaymentSerializer

    def handle_payment_result(self, session_id, success_message, error_message):
        if session_id:
            return Response({"message": success_message})
        else:
            return Response(
                {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
            )


class PaymentList(generics.ListCreateAPIView):
    """
    View for listing and creating Payment objects
    """

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.all()
        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)

        return queryset


class PaymentDetail(generics.RetrieveAPIView):
    """
    View for retrieving a single Payment object
    """

    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminOrSelf)

    def get_object(self):
        obj = get_object_or_404(Payment, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj


class CreateStripeSession(APIView):
    """
    API view for creating a Stripe session for payment processing
    """

    serializer_class = PaymentSerializer

    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)

        success_url = (
            request.build_absolute_uri(reverse("payments:payment_success"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = (
            request.build_absolute_uri(reverse("payments:payment_cancel"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        )

        if not success_url or not cancel_url:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        session = payment.create_stripe_session(success_url, cancel_url)

        return Response(
            {
                "session_id": session["id"],
                "session_url": session["url"],
            }
        )


class PaymentSuccess(BasePaymentView):
    """
    API view for handling successful payments
    """

    def get(self, request):
        session_id = request.GET.get("session_id")
        return self.handle_payment_result(
            session_id, "Payment was successful!", "Session ID not found."
        )


class PaymentCancel(BasePaymentView):
    """
    API view for handling canceled payments
    """

    def get(self, request):
        session_id = request.GET.get("session_id")
        return self.handle_payment_result(
            session_id,
            "Payment was not successful and can be paid later. "
            "The session is available for 24h.",
            "Session ID not found.",
        )
