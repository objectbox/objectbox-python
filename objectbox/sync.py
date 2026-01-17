import ctypes
from enum import Enum, auto, IntEnum

import objectbox.c as c
from objectbox import Store
from objectbox.c import OBX_sync_change_array


class SyncCredentials:
    """Credentials used to authenticate a sync client against a server."""

    def __init__(self, credential_type: c.SyncCredentialsType):
        self.type = credential_type

    @staticmethod
    def none() -> 'SyncCredentials':
        """No credentials - usually only for development purposes with a server
        configured to accept all connections without authentication.

        Returns:
            A SyncCredentials instance with no authentication.
        """
        return SyncCredentialsNone()

    @staticmethod
    def shared_secret_string(secret: str) -> 'SyncCredentials':
        """Shared secret authentication.

        Args:
            secret: The shared secret string.

        Returns:
            A SyncCredentials instance for shared secret authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.SHARED_SECRET_SIPPED, secret.encode('utf-8'))

    @staticmethod
    def google_auth(secret: str) -> 'SyncCredentials':
        """Google authentication.

        Args:
            secret: The Google authentication token.

        Returns:
            A SyncCredentials instance for Google authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.GOOGLE_AUTH, secret.encode('utf-8'))

    @staticmethod
    def user_and_password(username: str, password: str) -> 'SyncCredentials':
        """Username and password authentication.

        Args:
            username: The username.
            password: The password.

        Returns:
            A SyncCredentials instance for username/password authentication.
        """
        return SyncCredentialsUserPassword(c.SyncCredentialsType.USER_PASSWORD, username, password)

    @staticmethod
    def jwt_id_token(jwt_id_token: str) -> 'SyncCredentials':
        """JSON Web Token (JWT): an ID token that typically provides identity
        information about the authenticated user.

        Args:
            jwt_id_token: The JWT ID token.

        Returns:
            A SyncCredentials instance for JWT ID token authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_ID, jwt_id_token.encode('utf-8'))

    @staticmethod
    def jwt_access_token(jwt_access_token: str) -> 'SyncCredentials':
        """JSON Web Token (JWT): an access token that is used to access resources.

        Args:
            jwt_access_token: The JWT access token.

        Returns:
            A SyncCredentials instance for JWT access token authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_ACCESS, jwt_access_token.encode('utf-8'))

    @staticmethod
    def jwt_refresh_token(jwt_refresh_token: str) -> 'SyncCredentials':
        """JSON Web Token (JWT): a refresh token that is used to obtain a new
        access token.

        Args:
            jwt_refresh_token: The JWT refresh token.

        Returns:
            A SyncCredentials instance for JWT refresh token authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_REFRESH, jwt_refresh_token.encode('utf-8'))

    @staticmethod
    def jwt_custom_token(jwt_custom_token: str) -> 'SyncCredentials':
        """JSON Web Token (JWT): a token that is neither an ID, access,
        nor refresh token.

        Args:
            jwt_custom_token: The custom JWT token.

        Returns:
            A SyncCredentials instance for custom JWT token authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.JWT_CUSTOM, jwt_custom_token.encode('utf-8'))


class SyncCredentialsNone(SyncCredentials):
    """Internal use only. Represents no credentials for authentication."""

    def __init__(self):
        super().__init__(c.SyncCredentialsType.NONE)


class SyncCredentialsSecret(SyncCredentials):
    """Internal use only. Sync credential that is a single secret string."""

    def __init__(self, credential_type: c.SyncCredentialsType, secret: bytes):
        """Creates a secret-based credential.

        Args:
            credential_type: The type of credential.
            secret: UTF-8 encoded secret bytes.
        """
        super().__init__(credential_type)
        self.secret = secret


class SyncCredentialsUserPassword(SyncCredentials):
    """Internal use only. Sync credential with username and password."""

    def __init__(self, credential_type: c.SyncCredentialsType, username: str, password: str):
        """Creates a username/password credential.

        Args:
            credential_type: The type of credential.
            username: The username.
            password: The password.
        """
        super().__init__(credential_type)
        self.username = username
        self.password = password


class SyncState(Enum):
    """Current state of the SyncClient."""

    UNKNOWN = auto()
    """State is unknown, e.g. C-API reported a state that's not recognized yet."""

    CREATED = auto()
    """Client created but not yet started."""

    STARTED = auto()
    """Client started and connecting."""

    CONNECTED = auto()
    """Connection with the server established but not authenticated yet."""

    LOGGED_IN = auto()
    """Client authenticated and synchronizing."""

    DISCONNECTED = auto()
    """Lost connection, will try to reconnect if the credentials are valid."""

    STOPPED = auto()
    """Client in the process of being closed."""

    DEAD = auto()
    """Invalid access to the client after it was closed."""


class SyncRequestUpdatesMode:
    """Configuration of how SyncClient fetches remote updates from the server."""

    MANUAL = 'manual'
    """No updates, SyncClient.request_updates() must be called manually."""

    AUTO = 'auto'
    """Automatic updates, including subsequent pushes from the server, same as
    calling SyncClient.request_updates(True). This is the default unless
    changed by SyncClient.set_request_updates_mode()."""

    AUTO_NO_PUSHES = 'auto_no_pushes'
    """Automatic update after connection, without subscribing for pushes from the
    server. Similar to calling SyncClient.request_updates(False)."""


class SyncConnectionEvent:
    """Connection state change event."""

    CONNECTED = 'connected'
    """Connection to the server is established."""

    DISCONNECTED = 'disconnected'
    """Connection to the server is lost."""


class SyncLoginEvent:
    """Login state change event."""

    LOGGED_IN = 'logged_in'
    """Client has successfully logged in to the server."""

    CREDENTIALS_REJECTED = 'credentials_rejected'
    """Client's credentials have been rejected by the server.
    Connection will NOT be retried until new credentials are provided."""

    UNKNOWN_ERROR = 'unknown_error'
    """An unknown error occurred during authentication."""


class SyncCode(IntEnum):
    """Sync response/error codes."""

    OK = 20
    """Operation completed successfully."""

    REQ_REJECTED = 40
    """Request was rejected."""

    CREDENTIALS_REJECTED = 43
    """Credentials were rejected by the server."""

    UNKNOWN = 50
    """Unknown error occurred."""

    AUTH_UNREACHABLE = 53
    """Authentication server is unreachable."""

    BAD_VERSION = 55
    """Protocol version mismatch."""

    CLIENT_ID_TAKEN = 61
    """Client ID is already in use."""

    TX_VIOLATED_UNIQUE = 71
    """Transaction violated a unique constraint."""


class SyncChange:
    """Sync incoming data event."""

    def __init__(self, entity_id: int, puts: list[int], removals: list[int]):
        """Creates a SyncChange event.

        Args:
            entity_id: Entity ID this change relates to.
            puts: List of "put" (inserted/updated) object IDs.
            removals: List of removed object IDs.
        """
        self.entity_id = entity_id
        """Entity ID this change relates to."""

        self.puts = puts
        """List of "put" (inserted/updated) object IDs."""

        self.removals = removals
        """List of removed object IDs."""


class SyncLoginListener:
    """Listener for sync login events.

    Implement this class and pass to SyncClient.set_login_listener() to receive
    notifications about login success or failure.
    """

    def on_logged_in(self):
        """Called when the client has successfully logged in to the server."""
        pass

    def on_login_failed(self, sync_login_code: SyncCode):
        """Called when login has failed.

        Args:
            sync_login_code: The error code indicating why login failed.
        """
        pass


class SyncConnectionListener:
    """Listener for sync connection events.

    Implement this class and pass to SyncClient.set_connection_listener() to receive
    notifications about connection state changes.
    """

    def on_connected(self):
        """Called when the connection to the server is established."""
        pass

    def on_disconnected(self):
        """Called when the connection to the server is lost."""
        pass


class SyncErrorListener:
    """Listener for sync error events.

    Implement this class and pass to SyncClient.set_error_listener() to receive
    notifications about sync errors.
    """

    def on_error(self, sync_error_code: int):
        """Called when a sync error occurs.

        Args:
            sync_error_code: The error code indicating what error occurred.
        """
        pass


class SyncChangeListener:

    def on_change(self, sync_changes: list[SyncChange]):
        """Called when incoming data changes are received from the server.

        Args:
            sync_changes: List of SyncChange events representing the changes.
        """
        pass


class SyncClient:
    """Sync client is used to connect to an ObjectBox sync server.

    Use through the Sync class factory methods.
    """

    def __init__(self, store: Store, server_urls: list[str],
                 filter_variables: dict[str, str] | None = None):
        """Creates a Sync client associated with the given store and options.

        This does not initiate any connection attempts yet: call start() to do so.

        Args:
            store: The ObjectBox store to sync.
            server_urls: List of server URLs to connect to.
            filter_variables: Optional dictionary of filter variable names to values.
        """
        self.__c_change_listener = None
        self.__c_login_listener = None
        self.__c_login_failure_listener = None
        self.__c_connect_listener = None
        self.__c_disconnect_listener = None
        self.__c_error_listener = None
        if not server_urls:
            raise ValueError("Provide at least one server URL")

        if not Sync.is_available():
            raise RuntimeError(
                'Sync is not available in the loaded ObjectBox runtime library. '
                'Please visit https://objectbox.io/sync/ for options.')

        self.__store = store
        self.__server_urls = [url.encode('utf-8') for url in server_urls]

        self.__c_sync_client_ptr = c.obx_sync_urls(store.c_store(),
                                                   c.c_array_pointer(self.__server_urls, ctypes.c_char_p),
                                                   len(self.__server_urls))

        for name, value in (filter_variables or {}).items():
            self.add_filter_variable(name, value)

        self.__store.add_store_close_listener(on_store_close=self.__close_sync_client_func())

    def __del__(self):
        # Close the SyncClient when this instance is destructed
        # for ex. when garbage collected.
        self.close()

    def __close_sync_client_func(self):
        def close_sync_client():
            self.close()

        return close_sync_client

    def __check_sync_ptr_not_null(self):
        if self.__c_sync_client_ptr is None:
            raise ValueError('SyncClient already closed')

    def set_credentials(self, credentials: SyncCredentials):
        """Configure authentication credentials, depending on your server config.

        Args:
            credentials: The credentials to use for authentication.
        """
        self.__check_sync_ptr_not_null()
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

    def set_multiple_credentials(self, credentials_list: list[SyncCredentials]):
        """Like set_credentials, but accepts multiple credentials.

        However, does **not** support SyncCredentials.none().

        Args:
            credentials_list: List of credentials to use for authentication.

        Raises:
            ValueError: If credentials_list is empty or contains SyncCredentials.none().
        """
        self.__check_sync_ptr_not_null()
        if len(credentials_list) == 0:
            raise ValueError("Provide at least one credential")

        for i in range(len(credentials_list)):
            is_last = (i == len(credentials_list) - 1)
            credentials = credentials_list[i]

            if isinstance(credentials, SyncCredentialsNone):
                raise ValueError("SyncCredentials.none() is not supported, use set_credentials() instead")

            if isinstance(credentials, SyncCredentialsUserPassword):
                c.obx_sync_credentials_add_user_password(self.__c_sync_client_ptr,
                                                         credentials.type,
                                                         credentials.username.encode('utf-8'),
                                                         credentials.password.encode('utf-8'),
                                                         is_last
                                                         )
            elif isinstance(credentials, SyncCredentialsSecret):
                c.obx_sync_credentials_add(self.__c_sync_client_ptr,
                                           credentials.type,
                                           credentials.secret,
                                           len(credentials.secret),
                                           is_last)


    def set_request_updates_mode(self, mode: SyncRequestUpdatesMode):
        """Configures how sync updates are received from the server.

        If automatic updates are turned off, they will need to be requested manually.

        Args:
            mode: The request updates mode to use.
        """
        self.__check_sync_ptr_not_null()
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
        """Gets the current sync client state.

        Returns:
            The current SyncState of this client.
        """
        self.__check_sync_ptr_not_null()
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
        """Once the sync client is configured, you can start it to initiate synchronization.

        This method triggers communication in the background and returns immediately.
        The background thread will try to connect to the server, log-in and start
        syncing data (depends on SyncRequestUpdatesMode). If the device, network or
        server is currently offline, connection attempts will be retried later
        automatically. If you haven't set the credentials in the options during
        construction, call set_credentials() before start().
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_start(self.__c_sync_client_ptr)

    def stop(self):
        """Stops this sync client. Does nothing if it is already stopped."""
        self.__check_sync_ptr_not_null()
        c.obx_sync_stop(self.__c_sync_client_ptr)

    def trigger_reconnect(self) -> bool:
        """Triggers a reconnection attempt immediately.

        By default, an increasing backoff interval is used for reconnection attempts.
        But sometimes the code using this API has additional knowledge and can
        initiate a reconnection attempt sooner.

        Returns:
            True if a reconnect was actually triggered.
        """
        self.__check_sync_ptr_not_null()
        return c.check_obx_success(c.obx_sync_trigger_reconnect(self.__c_sync_client_ptr))

    def request_updates(self, subscribe_for_future_pushes: bool) -> bool:
        """Request updates since we last synchronized our database.

        Additionally, you can subscribe for future pushes from the server, to let
        it send us future updates as they come in.
        Call cancel_updates() to stop the updates.

        Args:
            subscribe_for_future_pushes: If True, also subscribe for future pushes.

        Returns:
            True if the request was successful.
        """
        self.__check_sync_ptr_not_null()
        return c.check_obx_success(c.obx_sync_updates_request(self.__c_sync_client_ptr, subscribe_for_future_pushes))

    def cancel_updates(self) -> bool:
        """Cancel updates from the server so that it will stop sending updates.

        See also request_updates().

        Returns:
            True if the cancellation was successful.
        """
        self.__check_sync_ptr_not_null()
        return c.check_obx_success(c.obx_sync_updates_cancel(self.__c_sync_client_ptr))

    @staticmethod
    def protocol_version() -> int:
        """Returns the protocol version this client uses."""
        return c.obx_sync_protocol_version()

    def protocol_server_version(self) -> int:
        """Returns the protocol version of the server after a connection is
        established (or attempted), zero otherwise.
        """
        return c.obx_sync_protocol_version_server(self.__c_sync_client_ptr)

    def close(self):
        """Closes and cleans up all resources used by this sync client.

        It can no longer be used afterwards, make a new sync client instead.
        Does nothing if this sync client has already been closed.
        """
        c.obx_sync_listener_error(self.__c_sync_client_ptr, ctypes.cast(None, c.OBX_sync_listener_error_t), None)
        c.obx_sync_listener_login(self.__c_sync_client_ptr, ctypes.cast(None, c.OBX_sync_listener_login_t), None)
        c.obx_sync_listener_login_failure(self.__c_sync_client_ptr,
                                          ctypes.cast(None, c.OBX_sync_listener_login_failure_t), None)
        c.obx_sync_listener_connect(self.__c_sync_client_ptr, ctypes.cast(None, c.OBX_sync_listener_connect_t), None)
        c.obx_sync_listener_disconnect(self.__c_sync_client_ptr, ctypes.cast(None, c.OBX_sync_listener_disconnect_t),
                                       None)
        c.obx_sync_listener_change(self.__c_sync_client_ptr, ctypes.cast(None, c.OBX_sync_listener_change_t), None)
        c.obx_sync_close(self.__c_sync_client_ptr)
        self.__c_sync_client_ptr = None

    def is_closed(self) -> bool:
        """Returns if this sync client is closed and can no longer be used."""
        return self.__c_sync_client_ptr is None

    def set_login_listener(self, login_listener: SyncLoginListener):
        """Sets a listener to observe login events (success/failure).

        Args:
            login_listener: The listener to receive login events.
        """
        self.__check_sync_ptr_not_null()
        self.__c_login_listener = c.OBX_sync_listener_login_t(lambda arg: login_listener.on_logged_in())
        self.__c_login_failure_listener = c.OBX_sync_listener_login_failure_t(
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
        """Sets a listener to observe connection state changes (connect/disconnect).

        Args:
            connection_listener: The listener to receive connection events.
        """
        self.__check_sync_ptr_not_null()
        self.__c_connect_listener = c.OBX_sync_listener_connect_t(lambda arg: connection_listener.on_connected())
        self.__c_disconnect_listener = c.OBX_sync_listener_disconnect_t(
            lambda arg: connection_listener.on_disconnected())
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
        """Sets a listener to observe sync error events.

        Args:
            error_listener: The listener to receive error events.
        """
        self.__check_sync_ptr_not_null()
        self.__c_error_listener = c.OBX_sync_listener_error_t(
            lambda arg, sync_error_code: error_listener.on_error(sync_error_code))
        c.obx_sync_listener_error(
            self.__c_sync_client_ptr,
            self.__c_error_listener,
            None
        )

    def set_change_listener(self, change_listener: SyncChangeListener):
        """Sets a listener to observe incoming data changes from the server.

        Args:
            change_listener: The listener to receive change events.
        """
        self.__check_sync_ptr_not_null()

        def c_change_callback(arg, sync_change_array_ptr):
            sync_change_array = ctypes.cast(sync_change_array_ptr, ctypes.POINTER(OBX_sync_change_array)).contents
            changes: list[SyncChange] = []
            for i in range(sync_change_array.count):
                c_sync_change: c.OBX_sync_change = sync_change_array.list[i]
                puts = []
                if c_sync_change.puts:
                    c_puts_id_array: c.OBX_id_array = ctypes.cast(c_sync_change.puts, c.OBX_id_array_p).contents
                    puts = list(
                        ctypes.cast(c_puts_id_array.ids, ctypes.POINTER(c.obx_id * c_puts_id_array.count)).contents)
                removals = []
                if c_sync_change.removals:
                    c_removals_id_array: c.OBX_id_array = ctypes.cast(c_sync_change.removals, c.OBX_id_array_p).contents
                    removals = list(
                        ctypes.cast(c_removals_id_array.ids,
                                    ctypes.POINTER(c.obx_id * c_removals_id_array.count)).contents)
                changes.append(SyncChange(
                    entity_id=c_sync_change.entity_id,
                    puts=puts,
                    removals=removals
                ))
            change_listener.on_change(changes)

        self.__c_change_listener = c.OBX_sync_listener_change_t(c_change_callback)
        c.obx_sync_listener_change(
            self.__c_sync_client_ptr,
            self.__c_change_listener,
            None
        )

    def wait_for_logged_in_state(self, timeout_millis: int):
        """Waits for the sync client to reach the logged-in state.

        Args:
            timeout_millis: Maximum time to wait in milliseconds.
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_wait_for_logged_in_state(self.__c_sync_client_ptr, timeout_millis)

    def add_filter_variable(self, name: str, value: str):
        """Adds or replaces a Sync filter variable value for the given name.

        Eventually, existing values for the same name are replaced.

        Sync client filter variables can be used in server-side Sync filters to
        filter out objects that do not match the filters. Filter variables must be
        added before login, so before calling start().

        See also remove_filter_variable() and remove_all_filter_variables().

        Args:
            name: The name of the filter variable.
            value: The value of the filter variable.
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_filter_variables_put(self.__c_sync_client_ptr, name.encode('utf-8'), value.encode('utf-8'))

    def remove_filter_variable(self, name: str):
        """Removes a previously added Sync filter variable value.

        See also add_filter_variable() and remove_all_filter_variables().

        Args:
            name: The name of the filter variable to remove.
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_filter_variables_remove(self.__c_sync_client_ptr, name.encode('utf-8'))

    def remove_all_filter_variables(self):
        """Removes all previously added Sync filter variable values.

        See also add_filter_variable() and remove_filter_variable().
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_filter_variables_remove_all(self.__c_sync_client_ptr)

    def get_outgoing_message_count(self, limit: int = 0) -> int:
        """Count the number of messages in the outgoing queue, i.e. those waiting
        to be sent to the server.

        By default, counts all messages without any limitation. For a lower number
        pass a limit that's enough for your app logic.

        Note: This call uses a (read) transaction internally:
            1) It's not just a "cheap" return of a single number. While this will
               still be fast, avoid calling this function excessively.
            2) The result follows transaction view semantics, thus it may not always
               match the actual value.

        Args:
            limit: Optional limit for counting messages. Default is 0 (no limit).

        Returns:
            The number of messages in the outgoing queue.
        """
        self.__check_sync_ptr_not_null()
        outgoing_message_count = ctypes.c_uint64(0)
        c.obx_sync_outgoing_message_count(self.__c_sync_client_ptr, limit, ctypes.byref(outgoing_message_count))
        return outgoing_message_count.value


class Sync:
    """ObjectBox Sync makes data available and synchronized across devices,
    online and offline.

    Start a client using Sync.client() and connect to a remote server.
    """
    __sync_clients: dict[Store, SyncClient] = {}

    @staticmethod
    def is_available() -> bool:
        """Returns True if the loaded ObjectBox native library supports Sync."""
        return c.obx_has_feature(c.Feature.Sync)

    @staticmethod
    def client(
            store: Store,
            server_url: str,
            credential: SyncCredentials,
            filter_variables: dict[str, str] | None = None
    ) -> SyncClient:
        """Creates a Sync client associated with the given store and configures it
        with the given options.

        This does not initiate any connection attempts yet, call SyncClient.start()
        to do so.

        Before SyncClient.start(), you can still configure some aspects of the
        client, e.g. its request updates mode.

        To configure Sync filter variables, pass variable names mapped to their
        value to filter_variables. Sync client filter variables can be used in
        server-side Sync filters to filter out objects that do not match the filter.

        Args:
            store: The ObjectBox store to sync.
            server_url: The URL of the sync server to connect to.
            credential: The credentials to use for authentication.
            filter_variables: Optional dictionary of filter variable names to values.

        Returns:
            A configured SyncClient instance.
        """
        client = SyncClient(store, [server_url], filter_variables)
        client.set_credentials(credential)
        return client

    @staticmethod
    def client_multi_creds(
            store: Store,
            server_url: str,
            credentials_list: list[SyncCredentials],
            filter_variables: dict[str, str] | None = None
    ) -> SyncClient:
        """Like client(), but accepts a list of credentials.

        When passing multiple credentials, does **not** support
        SyncCredentials.none().

        Args:
            store: The ObjectBox store to sync.
            server_url: The URL of the sync server to connect to.
            credentials_list: List of credentials to use for authentication.
            filter_variables: Optional dictionary of filter variable names to values.

        Returns:
            A configured SyncClient instance.
        """
        client = SyncClient(store, [server_url], filter_variables)
        client.set_multiple_credentials(credentials_list)
        return client

    @staticmethod
    def client_multi_urls(
            store: Store,
            server_urls: list[str],
            credential: SyncCredentials,
            filter_variables: dict[str, str] | None = None
    ) -> SyncClient:
        """Like client(), but accepts a list of URLs to work with multiple servers.

        Args:
            store: The ObjectBox store to sync.
            server_urls: List of server URLs to connect to.
            credential: The credentials to use for authentication.
            filter_variables: Optional dictionary of filter variable names to values.

        Returns:
            A configured SyncClient instance.
        """
        client = SyncClient(store, server_urls, filter_variables)
        client.set_credentials(credential)
        return client

    @staticmethod
    def client_multi_creds_multi_urls(
            store: Store,
            server_urls: list[str],
            credentials_list: list[SyncCredentials],
            filter_variables: dict[str, str] | None = None
    ) -> SyncClient:
        """Like client(), but accepts a list of credentials and a list of URLs to
        work with multiple servers.

        When passing multiple credentials, does **not** support
        SyncCredentials.none().

        Args:
            store: The ObjectBox store to sync.
            server_urls: List of server URLs to connect to.
            credentials_list: List of credentials to use for authentication.
            filter_variables: Optional dictionary of filter variable names to values.

        Returns:
            A configured SyncClient instance.

        Raises:
            ValueError: If a sync client is already active for the given store.
        """
        if store in Sync.__sync_clients:
            raise ValueError('Only one sync client can be active for a store')
        client = SyncClient(store, server_urls, filter_variables)
        client.set_multiple_credentials(credentials_list)
        Sync.__sync_clients[store] = client
        return client
