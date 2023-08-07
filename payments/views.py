from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment
from payments.permissions import IsAdminOrSelf
from payments.serializers import PaymentSerializer


class PaymentList(generics.ListCreateAPIView):
    """
    View for listing and creating Payment objects
    """

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(borrowing__user=user)


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
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

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


class PaymentSuccess(APIView):
    """
    API view for handling successful payments
    """

    serializer_class = PaymentSerializer

    def get(self, request):
        session_id = request.GET.get("session_id")
        if session_id:
            payment = Payment.objects.get(stripe_session_id=session_id)
            payment.status = Payment.PaymentStatus.PAID
            payment.save()
            return Response({"message": "Payment was successful!"})
        else:
            return Response(
                {"error": "Session ID not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PaymentCancel(APIView):
    """
    Retrieve the session ID from the query parameters
    """

    serializer_class = PaymentSerializer

    def get(self, request):
        session_id = request.GET.get("session_id")
        if session_id:
            return Response(
                {
                    "message": "Payment was not successful and can be paid later. "
                    "The session is available for 24h."
                }
            )
        else:
            return Response(
                {"error": "Session ID not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
