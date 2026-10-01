import flet as ft


class PremiumPage:
    def __init__(
        self,
        page,
        subscription_service,
        on_back,
        device_session_id,
    ):
        self.page = page
        self.subscription_service = subscription_service
        self.on_back = on_back
        self.device_session_id = device_session_id

        self.message = ft.Text("")

    def load_status(self):
        is_premium = (
            self.subscription_service.is_premium()
            and self.subscription_service.claim_device_session(
                self.device_session_id
            )
        )

        if is_premium:
            self.message.value = (
                "You are a Premium member."
            )
            self.message.color = ft.Colors.GREEN
        else:
            self.message.value = (
                "Premium access is not available on this device."
            )
            self.message.color = ft.Colors.ORANGE

    def build(self):
        self.load_status()

        buttons = []

        is_premium = (
            self.subscription_service.is_premium()
            and self.subscription_service.claim_device_session(
                self.device_session_id
            )
        )

        if is_premium:
            buttons.append(
                ft.Text(
                    "You already have Premium access.",
                    size=17,
                    color=ft.Colors.GREEN,
                )
            )
        else:
            buttons.append(
                ft.Button(
                    "Upgrade to Premium",
                    on_click=self.upgrade,
                )
            )

        return ft.Column(
            [
                ft.Button(
                    "← Back",
                    on_click=self.on_back,
                ),

                ft.Text(
                    "Premium",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    "Upgrade to Premium",
                    size=24,
                ),

                ft.Text(
                    "Premium features:",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    "• Access to premium quizzes\n"
                    "• Access to premium categories\n"
                    "• More quiz content",
                    size=17,
                ),

                ft.Divider(),

                self.message,

                *buttons,
            ],
            width=500,
            spacing=15,
        )

    def upgrade(self, e):
        try:
            self.subscription_service.activate_for_current_user()

            self.message.value = (
                "Premium activated successfully."
            )
            self.message.color = ft.Colors.GREEN

        except Exception as error:
            self.message.value = str(error)
            self.message.color = ft.Colors.RED

        self.page.update()