import ctypes
from enum import Enum, auto, IntEnum

import objectbox.c as c
from objectbox import Store


class SyncCredentials:

    def __init__(self, credential_type: c.SyncCredentialsType):
        self.type = credential_type

    @staticmethod
    def none() -> 'SyncCredentials':
        return SyncCredentialsNone()

    @staticmethod
    def shared_secret_string(secret: str) -> 'SyncCredentials':
        return SyncCredentialsSecret(c.SyncCredentialsType.SHARED_SECRET_SIPPED, secret.encode('utf-8'))

    @staticmethod
    def google_auth(secret: str) -> 'SyncCredentials':
        return SyncCredentialsSecret(c.SyncCredentialsType.GOOGLE_AUTH, secret.encode('utf-8'))

    @staticmethod
    def user_and_password(username: str, password: str) -> 'SyncCredentials':
        return SyncCredentialsUserPassword(c.SyncCredentialsType.USER_PASSWORD, username, password)

    @staticmethod
    def jwt_id_token(jwt_id_token: str) -> 'SyncCredentials':
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_ID, jwt_id_token.encode('utf-8'))

    @staticmethod
    def jwt_access_token(jwt_access_token: str) -> 'SyncCredentials':
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_ACCESS, jwt_access_token.encode('utf-8'))

    @staticmethod
    def jwt_refresh_token(jwt_refresh_token: str) -> 'SyncCredentials':
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_REFRESH, jwt_refresh_token.encode('utf-8'))

    @staticmethod
    def jwt_custom_token(jwt_custom_token: str) -> 'SyncCredentials':
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_CUSTOM, jwt_custom_token.encode('utf-8'))


class SyncCredentialsNone(SyncCredentials):
    def __init__(self):
        super().__init__(c.SyncCredentialsType.NONE)


class SyncCredentialsSecret(SyncCredentials):
    def __init__(self, credential_type: c.SyncCredentialsType, secret: bytes):
        super().__init__(credential_type)
        self.secret = secret


class SyncCredentialsUserPassword(SyncCredentials):
    def __init__(self, credential_type: c.SyncCredentialsType, username: str, password: str):
        super().__init__(credential_type)
        self.username = username
        self.password = password


class SyncState(Enum):
    UNKNOWN = auto()
    CREATED = auto()
    STARTED = auto()
    CONNECTED = auto()
    LOGGED_IN = auto()
    DISCONNECTED = auto()
    STOPPED = auto()
    DEAD = auto()


class SyncRequestUpdatesMode:
    MANUAL = 'manual'
    AUTO = 'auto'
    AUTO_NO_PUSHES = 'auto_no_pushes'


class SyncConnectionEvent:
    CONNECTED = 'connected'
    DISCONNECTED = 'disconnected'


class SyncLoginEvent:
    LOGGED_IN = 'logged_in'
    CREDENTIALS_REJECTED = 'credentials_rejected'
    UNKNOWN_ERROR = 'unknown_error'


class SyncCode(IntEnum):
    OK = 20
    REQ_REJECTED = 40
    CREDENTIALS_REJECTED = 43
    UNKNOWN = 50
    AUTH_UNREACHABLE = 53
    BAD_VERSION = 55
    CLIENT_ID_TAKEN = 61
    TX_VIOLATED_UNIQUE = 71


class SyncChange:
    def __init__(self, entity_id: int, entity: type, puts: list[int], removals: list[int]):
        self.entity_id = entity_id
        self.entity = entity
        self.puts = puts
        self.removals = removals


class SyncLoginListener:

    def on_logged_in(self):
        pass

    def on_login_failed(self, sync_login_code: SyncCode):
        pass


class SyncConnectionListener:

    def on_connected(self):
        pass

    def on_disconnected(self):
        pass


class SyncErrorListener:

    def on_error(self, sync_error_code: int):
        pass


class SyncClient:

    def __init__(self, store: Store, server_urls: list[str],
                 filter_variables: dict[str, str] | None = None):
        self.__c_login_listener = None
        self.__c_login_failure_listener = None
        self.__c_connect_listener = None
        self.__c_disconnect_listener = None
        self.__c_error_listener = None
        if not server_urls:
            raise ValueError("Provide at least one server URL")

        # TODO: Implement sync availability check
        # if not c.Sync.is_available():
        #     raise RuntimeError(
        #         'Sync is not available in the loaded ObjectBox runtime library. '
        #         'Please visit https://objectbox.io/sync/ for options.')

        self.__store = store
        self.__server_urls = [url.encode('utf-8') for url in server_urls]

        self.__c_sync_client_ptr = c.obx_sync_urls(store.c_store(),
                                                   c.c_array_pointer(self.__server_urls, ctypes.c_char_p),
                                                   len(self.__server_urls))

    def set_credentials(self, credentials: SyncCredentials):
        self.__credentials = credentials
        if isinstance(credentials, SyncCredentialsNone):
            c.obx_sync_credentials(self.__c_sync_client_ptr, credentials.type, None, 0)
        elif isinstance(credentials, SyncCredentialsUserPassword):
            c.obx_sync_credentials_user_password(self.__c_sync_client_ptr,
                                                 credentials.type,
                                                 credentials.username.encode('utf-8'),
                                                 credentials.password.encode('utf-8'))
        elif isinstance(credentials, SyncCredentialsSecret):
            c.obx_sync_credentials(self.__c_sync_client_ptr, credentials.type,
                                   credentials.secret,
                                   len(credentials.secret))

    def set_request_updates_mode(self, mode: SyncRequestUpdatesMode):
        if mode == SyncRequestUpdatesMode.MANUAL:
            c_mode = c.RequestUpdatesMode.MANUAL
        elif mode == SyncRequestUpdatesMode.AUTO:
            c_mode = c.RequestUpdatesMode.AUTO
        elif mode == SyncRequestUpdatesMode.AUTO_NO_PUSHES:
            c_mode = c.RequestUpdatesMode.AUTO_NO_PUSHES
        else:
            raise ValueError(f"Invalid mode: {mode}")
        c.obx_sync_request_updates_mode(self.__c_sync_client_ptr, c_mode)

    def get_sync_state(self) -> SyncState:
        c_state = c.obx_sync_state(self.__c_sync_client_ptr)
        if c_state == c.SyncState.CREATED:
            return SyncState.CREATED
        elif c_state == c.SyncState.STARTED:
            return SyncState.STARTED
        elif c_state == c.SyncState.CONNECTED:
            return SyncState.CONNECTED
        elif c_state == c.SyncState.LOGGED_IN:
            return SyncState.LOGGED_IN
        elif c_state == c.SyncState.DISCONNECTED:
            return SyncState.DISCONNECTED
        elif c_state == c.SyncState.STOPPED:
            return SyncState.STOPPED
        elif c_state == c.SyncState.DEAD:
            return SyncState.DEAD
        else:
            return SyncState.UNKNOWN

    def start(self):
        c.obx_sync_start(self.__c_sync_client_ptr)

    def stop(self):
        c.obx_sync_stop(self.__c_sync_client_ptr)

    def trigger_reconnect(self) -> bool:
        return c.check_obx_success(c.obx_sync_trigger_reconnect(self.__c_sync_client_ptr))

    @staticmethod
    def protocol_version() -> int:
        return c.obx_sync_protocol_version()

    def protocol_server_version(self) -> int:
        return c.obx_sync_protocol_version_server(self.__c_sync_client_ptr)

    def close(self):
        c.obx_sync_close(self.__c_sync_client_ptr)
        self.__c_sync_client_ptr = None

    def is_closed(self) -> bool:
        return self.__c_sync_client_ptr is None

    def set_login_listener(self, login_listener: SyncLoginListener):
        self.__c_login_listener = c.OBX_sync_listener_login(lambda arg: login_listener.on_logged_in())
        self.__c_login_failure_listener = c.OBX_sync_listener_login_failure(
            lambda arg, sync_login_code: login_listener.on_login_failed(sync_login_code))
        c.obx_sync_listener_login(
            self.__c_sync_client_ptr,
            self.__c_login_listener,
            None
        )
        c.obx_sync_listener_login_failure(
            self.__c_sync_client_ptr,
            self.__c_login_failure_listener,
            None
        )

    def set_connection_listener(self, connection_listener: SyncConnectionListener):
        self.__c_connect_listener = c.OBX_sync_listener_connect(lambda arg: connection_listener.on_connected())
        self.__c_disconnect_listener = c.OBX_sync_listener_disconnect(lambda arg: connection_listener.on_disconnected())
        c.obx_sync_listener_connect(
            self.__c_sync_client_ptr,
            self.__c_connect_listener,
            None
        )
        c.obx_sync_listener_disconnect(
            self.__c_sync_client_ptr,
            self.__c_disconnect_listener,
            None
        )

    def set_error_listener(self, error_listener: SyncErrorListener):
        self.__c_error_listener = c.OBX_sync_listener_error(
            lambda arg, sync_error_code: error_listener.on_error(sync_error_code))
        c.obx_sync_listener_error(
            self.__c_sync_client_ptr,
            self.__c_error_listener,
            None
        )

    def wait_for_logged_in_state(self, timeout_millis: int):
        c.obx_sync_wait_for_logged_in_state(self.__c_sync_client_ptr, timeout_millis)

    def add_filter_variable(self, name: str, value: str):
        c.obx_sync_filter_variables_put(self.__c_sync_client_ptr, name.encode('utf-8'), value.encode('utf-8'))

    def remove_filter_variable(self, name: str):
        c.obx_sync_filter_variables_remove(self.__c_sync_client_ptr, name.encode('utf-8'))

    def remove_all_filter_variables(self):
        c.obx_sync_filter_variables_remove_all(self.__c_sync_client_ptr)

    def get_outgoing_message_count(self, limit: int = 0) -> int:
        outgoing_message_count = ctypes.c_uint64(0)
        c.obx_sync_outgoing_message_count(self.__c_sync_client_ptr, limit, ctypes.byref(outgoing_message_count))
        return outgoing_message_count.value
