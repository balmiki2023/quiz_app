from supabase import Client
from services.device_identity import (
    save_login_credentials,
    get_login_credentials,
)

class AuthService:
    def __init__(self, supabase: Client, secure_storage,):
        self.supabase = supabase
        self.secure_storage = secure_storage

    def register(
        self,
        email: str,
        password: str,
        display_name: str,
    ):
        response = self.supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "display_name": display_name,
                    }
                },
            }
        )

        return response
        
    def login(self, email: str, password: str):
        return self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

    def logout(self):
        self.supabase.auth.sign_out()

    def get_current_user(self):
        return self.supabase.auth.get_user()
    
    def update_profile(self, display_name: str):
        response = self.supabase.auth.update_user(
            {
                "data": {
                    "display_name": display_name,
                }
            }
        )

        return response
        
    async def login_and_register_device(
        self, email, password, device_session_id
    ):
        # Step 1: Authenticate
        response = self.login(email, password)

        if not response.session:
            raise Exception("Login did not create an authenticated session.")

        # Step 2: Verify device
        claim_response = self.supabase.rpc(
            "claim_device_user",
            {
                "target_device_session_id": device_session_id
            }
        ).execute()

        # Step 3: Reject unauthorized devices
        if claim_response.data is not True:
            self.supabase.auth.sign_out()
            raise Exception(
                "This account is already registered on another device."
            )

        # Step 4: Save credentials only after successful verification
        await save_login_credentials(
            email,
            password,
            self.secure_storage,
        )
        return response

    async def auto_login(self, device_session_id, secure_storage):
        credentials = await get_login_credentials(secure_storage)

        if not credentials:
            return None

        try:
            return await self.login_and_register_device(
                email=credentials["email"],
                password=credentials["password"],
                device_session_id=device_session_id,
            )

        except Exception as error:
            print("AUTO LOGIN FAILED:", repr(error))
            return None


