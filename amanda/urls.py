"""amanda URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from response.views import *
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('admin/', admin.site.urls),
    path('response/', csrf_exempt(simple_response)),
    path('assistant_response/', csrf_exempt(assistant_response)),
    path('game_response/', csrf_exempt(game_response)),
    path('auth/', csrf_exempt(auth)),
    path('consent_form/<int:experiment_id>/', consent_form),
    path('speech_access_token/', speech_access_token),
    path('conversation_finished/', csrf_exempt(conversation_finished)),
    path('about/<str:version>/', about),
]
