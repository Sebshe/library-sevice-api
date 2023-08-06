from rest_framework import routers

from books.views import BookViewSet

router = routers.DefaultRouter()
router.register(r"", BookViewSet, basename="book")

urlpatterns = router.urls

app_name = "books"
