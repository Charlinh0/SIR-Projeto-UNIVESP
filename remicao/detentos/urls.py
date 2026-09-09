from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Nossa nova rota de login
    path("accounts/login/", auth_views.LoginView.as_view(template_name='detentos/login.html'), name="login"),

    # Página inicial (deixei só a correta para não dar conflito)
    path("", views.home, name="home"),

    # Restante do sistema
    path("detentos/", views.lista_detentos, name="lista_detentos"),
    path("detento/<int:detento_id>/", views.detalhe_detento, name="detalhe_detento"),
    path("detento/<int:detento_id>/notificar/", views.notificar_elegibilidade, name="notificar_elegibilidade"),
    path("consulta/", views.consulta_detento, name="consulta_detento"),
]