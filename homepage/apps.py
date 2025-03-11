from django.apps import AppConfig
# from sceneid.apps import SceneIDConfig

class HomepageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'homepage'

    def ready(self):
        import homepage.signals

# class DemositeSceneIDConfig(SceneIDConfig):
#     connect_login_form_class = 'homepage.forms.LoginForm'
#     connect_register_form_class = 'homepage.forms.SceneIDUserCreationForm'