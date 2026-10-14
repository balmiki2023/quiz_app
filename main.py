"""Application entry point for the Flet Quiz App."""

import flet as ft
from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL
from pages.home import HomePage
from pages.login import LoginPage
from pages.premium import PremiumPage
from pages.profile import ProfilePage
from pages.register import RegisterPage
from services.admin_service import AdminService
from services.attempt_service import QuizAttemptService
from services.auth import AuthService
from services.device_identity import (
    get_device_session_id,
    is_device_associated,
    mark_device_associated,
)
from services.quiz_service import QuizService
from services.subscription_service import SubscriptionService

def main(page: ft.Page) -> None:
    """Configure the app and connect page navigation callbacks."""
    page.title = "Quiz App"
    page.padding = 30

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    auth_service = AuthService(supabase)
    quiz_service = QuizService(supabase)
    attempt_service = QuizAttemptService(supabase)
    subscription_service = SubscriptionService(supabase)
    admin_service = AdminService(supabase)
    device_session_id = get_device_session_id()

    def show_login() -> None:
        page.clean()
        login_page = LoginPage(
            page,
            auth_service,
            show_home,
            show_register,
            is_device_associated(),
        )
        page.add(login_page.build())
        page.update()

    def show_register() -> None:
        if is_device_associated():
            show_login()
            return

        page.clean()
        register_page = RegisterPage(
            page,
            auth_service,
            show_login,
            show_login,
        )
        page.add(register_page.build())
        page.update()

    def show_home() -> None:
        page.clean()
        device_allowed = subscription_service.claim_device_user(
            device_session_id
        )

        if device_allowed:
            mark_device_associated()
        else:
            page.add(
                ft.Column(
                    [
                        ft.Text(
                            "This device is already associated with another user.",
                            color=ft.Colors.RED,
                            size=18,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            page.update()
            return

        home_page = HomePage(
            page,
            quiz_service,
            attempt_service,
            subscription_service,
            show_profile,
            show_home,
            device_session_id,
        )
        page.add(home_page.build())
        page.update()

    def show_profile() -> None:
        page.clean()
        profile_page = ProfilePage(
            page,
            auth_service,
            quiz_service,
            subscription_service,
            admin_service,
            supabase,
            show_home,
            show_login,
            show_premium,
        )
        page.add(profile_page.build())
        page.update()

    def show_premium() -> None:
        page.clean()
        premium_page = PremiumPage(
            page,
            subscription_service,
            show_profile,
            device_session_id,
        )
        page.add(premium_page.build())
        page.update()

    show_login()

if __name__ == "__main__":
    ft.run(main)
