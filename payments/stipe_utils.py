import stripe

from library_service_api import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(
    payment_type, money_to_pay, book_title, success_url, cancel_url
):
    line_items = [
        {
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"{payment_type} for {book_title}",
                },
                "unit_amount": int(money_to_pay * 100),
            },
            "quantity": 1,
        }
    ]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return session
