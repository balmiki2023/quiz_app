import os
import platform
import uuid

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
            return __import__("json").load(file)
    except (OSError, ValueError):
        return {}

def _save_device_data(data):
    path = _get_device_file()

    with open(path, "w", encoding="utf-8") as file:
        __import__("json").dump(data, file)

def get_device_session_id():
    data = _load_device_data()

    device_session_id = data.get("device_session_id")

    if device_session_id:
        print("DEVICE IDENTITY FILE:", _get_device_file)
        print("CURRENT DEVICE SESSION ID:", device_session_id)
        return device_session_id

    device_session_id = str(uuid.uuid4())
    print("DEVICE IDENTITY FILE:", _get_device_file)
    print("GENERATED DEVICE SESSION ID:", device_session_id)


    data["device_session_id"] = device_session_id

    _save_device_data(data)

    return device_session_id

def is_device_associated():
    data = _load_device_data()

    return data.get("device_associated", False)

def mark_device_associated():
    data = _load_device_data()

    data["device_associated"] = True

    _save_device_data(data)