import uuid

from supabase import Client


class SubscriptionService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def get_current_user_id(self):
        response = self.supabase.auth.get_user()

        if not response or not response.user:
            return None

        return response.user.id

    def get_subscription(self, user_id=None):
        if user_id is None:
            user_id = self.get_current_user_id()

        if not user_id:
            return None

        response = (
            self.supabase
            .table("subscriptions")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def is_premium(self, user_id=None):
        subscription = self.get_subscription(user_id)

        if not subscription:
            return False

        return subscription.get("status") == "active"

    def create_device_session_id(self):
        return str(uuid.uuid4())

    def claim_device_session(self, device_session_id):
        print("CLAIMING DEVICE:", device_session_id)

        response = self.supabase.rpc(
            "claim_subscription_session",
            {
                "target_device_session_id": device_session_id,
            },
        ).execute()

        print("CLAIM RESULT:", response.data)

        return response.data
        
    def claim_device_user(self, device_session_id):
        response = self.supabase.rpc(
            "claim_device_user",
            {
                "target_device_session_id": device_session_id,
            },
        ).execute()

        return response.data

    def release_device_session(self):
        response = self.supabase.rpc(
            "release_subscription_session"
        ).execute()

        return response.data

    def activate_for_current_user(self):
        user_id = self.get_current_user_id()

        if not user_id:
            raise Exception("No authenticated user.")

        response = self.supabase.rpc(
            "activate_subscription",
            {
                "target_user_id": str(user_id),
            },
        ).execute()

        return response