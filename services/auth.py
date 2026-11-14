from supabase import Client

class AuthService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

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
        
    def login_and_register_device(
        self, email, password, device_session_id
    ):
        # Step 1: Authenticate with email and password
        response = self.login(email, password)

        if not response.session:
            raise Exception("Login did not create an authenticated session.")

        # Step 2: Check whether this device is allowed
        try:
            claim_response = self.supabase.rpc(
                "claim_device_user",
                {
                    "target_device_session_id": device_session_id
                }
            ).execute()
            print("LOGGED-IN USER ID:", response.user.id)
            print("DEVICE SESSION ID:", device_session_id)

            print("DEVICE CLAIM RESPONSE:", repr(claim_response.data))

        except Exception as error:
            print("DEVICE CLAIM ERROR:", repr(error))
            raise

        # Step 3: Reject unauthorized devices
        if claim_response.data is not True:
            self.supabase.auth.sign_out()
            raise Exception(
                "This account is already registered on another device."
            )

        return response


