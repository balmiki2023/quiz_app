import flet as ft

from services.auth import AuthService


class LoginPage:
    def __init__(
        self,
        page: ft.Page,
        auth_service: AuthService,
        on_login,
        on_register,
        device_associated=False,
    ):
        self.page = page
        self.auth_service = auth_service
        self.on_login = on_login
        self.on_register = on_register
        self.device_associated = device_associated

        self.email = ft.TextField(
            label="Email",
            keyboard_type=ft.KeyboardType.EMAIL,
        )

        self.password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
        )

        self.message = ft.Text("")

    def login(self, e):
        try:
            self.auth_service.login(
                self.email.value,
                self.password.value,
            )

            self.message.value = "Login successful!"
            self.message.color = ft.Colors.GREEN

            self.on_login()

        except Exception as error:
            self.message.value = str(error)
            self.message.color = ft.Colors.RED

        self.page.update()

    def register(self, e):
        self.on_register()

    def build(self):
        return ft.Column(
            [
                ft.Text(
                    "Quiz App",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Login",
                    size=24,
                ),
                self.email,
                self.password,
                ft.Button(
                    "Login",
                    on_click=self.login,
                ),
                ft.TextButton(
                    "Create an account",
                    on_click=self.register,
                ) if not self.device_associated else ft.Container(),
                self.message,
            ],
            width=400,
            spacing=15,
        )