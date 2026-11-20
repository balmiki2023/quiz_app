"""Application entry point for the Flet Quiz App."""

import flet as ft
import flet_secure_storage as fss
from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL
from pages.home import HomePage
from pages.login import LoginPage
from pages.premium import PremiumPage
from pages.profile import ProfilePage
from pages.register import RegisterPage
from pages.saved_questions import SavedQuestionsPage
from services.admin_service import AdminService
from services.auth import AuthService
from services.device_identity import (
    get_device_session_id,
    get_login_credentials,
    migrate_device_data_to_secure_storage,
    is_device_associated,
    mark_device_associated,
)
from services.device_identity import (
    get_login_credentials,
)
from services.quiz_service import QuizService
from services.subscription_service import SubscriptionService
from services.local_database_service import LocalDatabaseService
from services.device_identity import migrate_device_data_to_secure_storage


async def main(page: ft.Page) -> None:
    page.title = "Quiz App"
    page.padding = 30

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    secure_storage = fss.SecureStorage()
    page.services.append(secure_storage)

    # try:
    #     test_value = await secure_storage.get("quizapp.device_session_id")
    #     print("SECURE STORAGE GET:", repr(test_value))

    # except Exception as error:
    #     print("SECURE STORAGE TEST FAILED:", repr(error))

    # migration_success = await migrate_device_data_to_secure_storage(
    #     secure_storage
    # )

    # if not migration_success:
    #     raise RuntimeError(
    #         "Could not migrate device data to secure storage."
    #     )

    device_session_id = await get_device_session_id(secure_storage)

    local_db = LocalDatabaseService()
    local_db.initialize()

    auth_service = AuthService(supabase, secure_storage)
    quiz_service = QuizService(supabase)
    subscription_service = SubscriptionService(supabase)
    admin_service = AdminService(supabase)   


    def show_login() -> None:
        page.clean()
        login_page = LoginPage(
            page,
            auth_service,
            lambda: show_home(sync_after_login=True),
            show_register,
            device_session_id=device_session_id,
            device_associated=is_device_associated(),
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
            secure_storage,
            lambda: page.run_task(show_saved_login),
            lambda: page.run_task(show_saved_login),
        )

        page.add(register_page.build())
        page.update()

    def show_home(sync_after_login=False) -> None:
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
                        ft.Button(
                            "← Back",
                            on_click=show_login,
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
            subscription_service,
            local_db,
            show_profile,
            show_home,
            device_session_id,
        )

        if sync_after_login:
            home_page.sync_data_in_background()

        page.add(home_page.build())
        page.update()

    async def show_saved_login():
        print("SHOW SAVED LOGIN CALLED")

        credentials = await get_login_credentials(secure_storage)
        print("CREDENTIALS:", credentials is not None)

        if not credentials:
            print("NO CREDENTIALS — SHOWING REGISTER")
            show_register()
            return


        async def handle_login(e):
            login_button.disabled = True
            login_button.text = "Logging in..."
            page.update()

            response = await auth_service.auto_login(
                device_session_id,
                secure_storage,
            )

            if response and response.session:
                show_home(sync_after_login=True)
            else:
                show_login()

        login_button = ft.Button(
            "Login",
            on_click=handle_login,
            width=200,
        )

        page.clean()

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"Welcome, {credentials.get('display_name') or 'User'}!",
                            size=26,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            credentials["email"],
                            size=18,
                        ),
                        login_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    expand=True,
                ),
                expand=True,
                alignment=ft.Alignment.CENTER,
            )
        )

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
            lambda: page.run_task(show_saved_login),
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

    async def clear_secure_storage():
        await secure_storage.clear()
        print("Secure storage cleared.")

    # await clear_secure_storage()    
    await show_saved_login()
   
if __name__ == "__main__":
    ft.run(main)
