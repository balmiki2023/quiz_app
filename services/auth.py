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

    def login_t(
        self,
        email: str,
        password: str,
    ):
        response = self.supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        return response

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