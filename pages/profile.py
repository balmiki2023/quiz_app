import flet as ft

from admin.dashboard import AdminDashboard

from services.auth import AuthService
from services.subscription_service import SubscriptionService


class ProfilePage:
    def __init__(
        self,
        page,
        auth_service: AuthService,
        quiz_service,
        subscription_service: SubscriptionService,
        admin_service,
        supabase,
        on_back,
        on_logout,
        on_premium,
    ):
        self.page = page
        self.auth_service = auth_service
        self.quiz_service = quiz_service
        self.subscription_service = subscription_service
        self.admin_service = admin_service
        self.supabase = supabase
        self.on_back = on_back
        self.on_logout = on_logout
        self.on_premium = on_premium

        self.display_name = ft.TextField(
            label="Display name",
        )

        self.email = ft.TextField(
            label="Email",
            read_only=True,
        )
        
        self.subscription_status = ft.Text(
            "Subscription: Free",
        )

        self.message = ft.Text("")

    def load_profile(self):
        response = self.auth_service.get_current_user()

        if not response or not response.user:
            return

        user = response.user

        self.email.value = user.email or ""

        metadata = user.user_metadata or {}

        self.display_name.value = (
            metadata.get("display_name") or ""
        )
        
        is_premium = (
            self.subscription_service.is_premium(
                user.id
            )
        )

        if is_premium:
            self.subscription_status.value = (
                "Subscription: Premium"
            )
            self.subscription_status.color = (
                ft.Colors.GREEN
            )
        else:
            self.subscription_status.value = (
                "Subscription: Free"
            )
            self.subscription_status.color = (
                ft.Colors.ORANGE
            )
        
    
    def open_admin_panel(self, e=None):
        dashboard = AdminDashboard(
            self.page,
            self.admin_service,
            self.quiz_service,
            self.supabase,
            self.on_back,
        )

        self.page.clean()
        self.page.add(dashboard.build())
        self.page.update()
    
    def save_profile(self, e):
        try:
            self.auth_service.update_profile(
                self.display_name.value
            )

            self.message.value = (
                "Profile updated successfully."
            )
            self.message.color = ft.Colors.GREEN

        except Exception as error:
            self.message.value = str(error)
            self.message.color = ft.Colors.RED

        self.page.update()

    def logout(self, e):
        try:
            self.subscription_service.release_device_session()
            self.auth_service.logout()
            self.on_logout()

        except Exception as error:
            self.message.value = str(error)
            self.message.color = ft.Colors.RED
            self.page.update()

    def build(self):
        self.load_profile()
        is_admin = self.admin_service.is_admin()

        controls = [
            ft.Button(
                "← Back",
                on_click=self.on_back,
            ),

            ft.Text(
                "Profile",
                size=30,
                weight=ft.FontWeight.BOLD,
            ),

            self.display_name,

            self.email,

            self.subscription_status,

            ft.Button(
                "View Premium",
                on_click=lambda e: self.on_premium(),
            ),

            ft.Button(
                "Save Profile",
                on_click=self.save_profile,
            ),

            self.message,

            ft.Divider(),
        ]

        if is_admin:
            controls.append(
                ft.Button(
                    "Admin Panel",
                    on_click=self.open_admin_panel,
                )
            )

        controls.append(
            ft.Button(
                "Logout",
                on_click=self.logout,
            )
        )

        return ft.Column(
            controls,
            width=500,
            spacing=15,
        )