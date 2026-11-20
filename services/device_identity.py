import os
import platform
import uuid
import json

APP_NAME = "QuizApp"

def _get_storage_dir():
    # Use Flet's writable, persistent application storage.
    storage_dir = os.environ.get("FLET_APP_STORAGE_DATA")

    if storage_dir:
        return storage_dir

    # Fallback for running outside Flet on Windows.
    if platform.system() == "Windows":
        return os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")),
            APP_NAME,
        )

    # Fallback for macOS.
    if platform.system() == "Darwin":
        return os.path.join(
            os.path.expanduser("~/Library/Application Support"),
            APP_NAME,
        )

    raise RuntimeError(
        "FLET_APP_STORAGE_DATA is not available. "
        "Cannot determine a writable application storage directory."
    )

def _get_device_file():
    storage_dir = _get_storage_dir()
    os.makedirs(storage_dir, exist_ok=True)

    return os.path.join(
        storage_dir,
        "device.json",
    )

def _load_device_data():
    path = _get_device_file()

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return {}


def _save_device_data(data):
    path = _get_device_file()

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

async def get_device_session_id(secure_storage):
    device_session_id = await secure_storage.get(
        "quizapp.device_session_id"
    )

    if device_session_id:
        return device_session_id

    # Recover the existing ID from device.json if available
    data = _load_device_data()
    device_session_id = data.get("device_session_id")

    if device_session_id:
        await secure_storage.set(
            "quizapp.device_session_id",
            device_session_id,
        )
        return device_session_id

    # Generate a new ID only when no existing ID is available
    device_session_id = str(uuid.uuid4())

    await secure_storage.set(
        "quizapp.device_session_id",
        device_session_id,
    )

    return device_session_id

def is_device_associated():
    data = _load_device_data()

    return data.get("device_associated", False)

def mark_device_associated():
    data = _load_device_data()

    data["device_associated"] = True

    _save_device_data(data)

async def save_login_credentials(
    email,
    password,
    secure_storage,
    display_name=None,
):
    await secure_storage.set("quizapp.email", email)
    await secure_storage.set("quizapp.password", password)

    # Keep display name in device.json.
    if display_name:
        data = _load_device_data()
        data["display_name"] = display_name
        _save_device_data(data)

async def get_login_credentials(secure_storage):
    email = await secure_storage.get("quizapp.email")
    password = await secure_storage.get("quizapp.password")

    if not email or not password:
        return None

    data = _load_device_data()

    return {
        "email": email,
        "password": password,
        "display_name": data.get("display_name", ""),
    }

async def migrate_device_data_to_secure_storage(secure_storage):
    """
    Copy sensitive values from device.json to secure storage.
    Keep the original JSON values until the migration is verified.
    """

    data = _load_device_data()

    sensitive_values = {
        "quizapp.device_session_id": data.get("device_session_id"),
        "quizapp.email": data.get("email"),
        "quizapp.password": data.get("password"),
    }

    try:
        for key, value in sensitive_values.items():
            if value is None:
                continue

            existing_value = await secure_storage.get(key)

            if existing_value is None:
                await secure_storage.set(key, value)

        # Verify that every value from JSON reached secure storage.
        for key, value in sensitive_values.items():
            if value is None:
                continue

            stored_value = await secure_storage.get(key)

            if stored_value != value:
                raise RuntimeError(
                    f"Secure storage verification failed for {key}"
                )

        return True

    except Exception as error:
        print("SECURE STORAGE MIGRATION FAILED:", repr(error))
        return False