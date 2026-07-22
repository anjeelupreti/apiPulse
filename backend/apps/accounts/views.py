from rest_framework import generics
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    # the one endpoint that has to be open to anyone, obviously — can't
    # require a login to sign up in the first place
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
