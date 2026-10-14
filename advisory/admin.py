from django.contrib import admin
from .models import CommunityQuestion, CommunityReply, Consultation
admin.site.register([Consultation, CommunityQuestion, CommunityReply])
