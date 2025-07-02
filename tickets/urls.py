from django.urls import path
from .views import (
    TicketListView,
    TicketDetailView,
    cerrar_ticket,
    reabrir_ticket,
    cambiar_estado,
)

app_name = 'tickets'

urlpatterns = [
    path('', TicketListView.as_view(), name='ticket_list'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:pk>/cerrar/', cerrar_ticket, name='cerrar_ticket'),
    path('<int:pk>/reabrir/', reabrir_ticket, name='reabrir_ticket'),
    path('<int:pk>/cambiar-estado/<str:nuevo_estado>/', cambiar_estado, name='cambiar_estado'),
]
