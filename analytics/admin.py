from django.contrib import admin

from .models import Forecast, RiskAlert

admin.site.register(Forecast)
admin.site.register(RiskAlert)
