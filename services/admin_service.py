from supabase import Client


class AdminService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def get_current_user_id(self):
        response = self.supabase.auth.get_user()

        if not response or not response.user:
            return None

        return response.user.id

    def is_admin(self):
        user_id = self.get_current_user_id()

        if not user_id:
            return False

        response = (
            self.supabase
            .table("profiles")
            .select("is_admin")
            .eq("id", str(user_id))
            .limit(1)
            .execute()
        )

        if not response.data:
            return False

        return response.data[0].get("is_admin", False)