from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^home/', views.home, name='home'),
    url(r'^enrol/', views.enrol, name='enrol'),
    url(r'^train/(?:(?P<userId>\d+)/)?', views.train, name='train'),
    url(r'^test/(?P<userId>\d+)/', views.test, name='test'),
]