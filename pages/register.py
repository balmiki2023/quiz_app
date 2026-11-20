import flet as ft

from services.auth import AuthService
from services.device_identity import save_login_credentials

class RegisterPage:
    def __init__(
        self,
        page: ft.Page,
        auth_service: AuthService,
        secure_storage,
        on_registered,
        on_back,
    ):
        self.page = page
        self.auth_service = auth_service
        self.secure_storage = secure_storage
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

    async def register(self, e):
        try:
            response = self.auth_service.register(
                self.email.value,
                self.password.value,
                self.display_name.value,
            )

            # Verify registration succeeded
            if not response or not response.user:
                raise Exception("Registration failed. Please try again.")

            # Save credentials only after successful registration
            await save_login_credentials(
                self.email.value,
                self.password.value,
                self.secure_storage,
                display_name=self.display_name.value,
            )

            # Navigate to saved-login screen
            print("REGISTRATION CALLBACK TRIGGERED")
            self.on_registered()

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
                self.message,
            ],
            width=400,
            spacing=15,
        )