from django.urls import path
from .views import (
    PaymentList,
    PaymentDetail,
    CreateStripeSession,
    PaymentSuccess,
    PaymentCancel,
)

urlpatterns = [
    path("", PaymentList.as_view(), name="payment_list"),
    path("<int:pk>/", PaymentDetail.as_view(), name="payment_detail"),
    path(
        "<int:pk>/create-stripe-session/",
        CreateStripeSession.as_view(),
        name="create_stripe_session",
    ),
    path("success/", PaymentSuccess.as_view(), name="payment_success"),
    path("cancel/", PaymentCancel.as_view(), name="payment_cancel"),
]

app_name = "payments"
