from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    # the one endpoint that has to be open to anyone, obviously — can't
    # require a login to sign up in the first place
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class GoogleLoginView(APIView):
    # frontend gets an ID token from Google's own JS (Identity Services),
    # we just verify it's genuinely from Google and meant for our app -
    # no OAuth redirect dance, no client secret needed for this part.
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'detail': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = google_id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response({'detail': 'invalid Google token'}, status=status.HTTP_401_UNAUTHORIZED)

        email = payload['email']
        # username=email as the account key - first Google login for an
        # email creates the account, every login after that finds the same
        # one. set_unusable_password so nobody can log in to it any other
        # way (no password was ever chosen for this account).
        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'first_name': payload.get('given_name', '')},
        )
        if created:
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({'access': str(refresh.access_token), 'refresh': str(refresh)})
