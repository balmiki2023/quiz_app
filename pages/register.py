import flet as ft

from services.auth import AuthService


class RegisterPage:
    def __init__(
        self,
        page: ft.Page,
        auth_service: AuthService,
        on_registered,
        on_back,
    ):
        self.page = page
        self.auth_service = auth_service
        self.on_registered = on_registered
        self.on_back = on_back

        self.display_name = ft.TextField(
            label="Display name",
        )

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

    def register(self, e):
        try:
            self.auth_service.register(
                self.email.value,
                self.password.value,
                self.display_name.value,
            )

            self.message.value = (
                "Registration successful. "
                "You can now log in."
            )
            self.message.color = ft.Colors.GREEN

            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.message.color = ft.Colors.RED

            self.page.update()

    def back(self, e):
        self.on_back()

    def build(self):
        return ft.Column(
            [
                ft.Text(
                    "Create Account",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),
                self.display_name,
                self.email,
                self.password,
                ft.Button(
                    "Register",
                    on_click=self.register,
                ),
                ft.TextButton(
                    "Back to Login",
                    on_click=self.back,
                ),
                self.message,
            ],
            width=400,
            spacing=15,
        )