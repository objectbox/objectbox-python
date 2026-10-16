import ctypes
import threading
import typing
from enum import Enum, auto, IntEnum

import objectbox.c as c
from objectbox import Store
from objectbox.c import OBX_sync_change_array


def _to_bytes(value: typing.Union[str, bytes]) -> bytes:
    if isinstance(value, str):
        return value.encode('utf-8')
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    raise TypeError(f"Expected str or bytes, got {type(value).__name__}")


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
    def shared_secret(secret: typing.Union[str, bytes]) -> 'SyncCredentials':
        """Shared secret authentication.

        Args:
            secret: The shared secret, a string or bytes.

        Returns:
            A SyncCredentials instance for shared secret authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.SHARED_SECRET_SIPPED, _to_bytes(secret))

    @staticmethod
    def google_auth(token: typing.Union[str, bytes]) -> 'SyncCredentials':
        """Google authentication.

        Args:
            token: The Google ID token, a string or bytes.

        Returns:
            A SyncCredentials instance for Google authentication.
        """
        return SyncCredentialsSecret(c.SyncCredentialsType.GOOGLE_AUTH, _to_bytes(token))

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


class SyncRequestUpdatesMode(IntEnum):
    """Configuration of how SyncClient fetches remote updates from the server."""

    MANUAL = c.RequestUpdatesMode.MANUAL
    """No updates, SyncClient.request_updates() must be called manually."""

    AUTO = c.RequestUpdatesMode.AUTO
    """Automatic updates, including subsequent pushes from the server, same as
    calling SyncClient.request_updates(True). This is the default unless
    changed by SyncClient.set_request_updates_mode()."""

    AUTO_NO_PUSHES = c.RequestUpdatesMode.AUTO_NO_PUSHES
    """Automatic update after connection, without subscribing for pushes from the
    server. Similar to calling SyncClient.request_updates(False)."""


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


def _to_sync_code(code: int) -> typing.Union[SyncCode, int]:
    """Converts to SyncCode; unknown codes (e.g. added by a newer library) are passed as int."""
    try:
        return SyncCode(code)
    except ValueError:
        return code


class SyncChange:
    """Sync incoming data event."""

    def __init__(self, entity_id: int, puts: typing.List[int], removals: typing.List[int]):
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

    Note: like all Sync listeners, it is called from the sync client's background thread; it should return quickly
    and must not close the client.
    """

    def on_logged_in(self):
        """Called when the client has successfully logged in to the server."""
        pass

    def on_login_failed(self, sync_login_code: SyncCode):
        """Called when login has failed.

        Args:
            sync_login_code: The error code indicating why login failed (an int if the code is unknown).
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


class SyncCompletedListener:
    """Listener for sync completed events.

    Implement this class and pass to SyncClient.set_completed_listener() to be notified when synchronization has
    completed. Note: called from the sync client's background thread (see SyncLoginListener).
    """

    def on_updates_completed(self):
        """Called each time a sync has completed, i.e. the client caught up with the current server state
        (the client is "up-to-date")."""
        pass


class SyncChangeListener:
    """Listener for incoming data changes from the server.

    Implement this class and pass to SyncClient.set_change_listener(). Note: called from the sync client's background
    thread (see SyncLoginListener).
    """

    def on_change(self, sync_changes: typing.List[SyncChange]):
        """Called when incoming data changes are received from the server.

        Args:
            sync_changes: List of SyncChange events representing the changes.
        """
        pass


class SyncClient:
    """Sync client is used to connect to an ObjectBox sync server.

    Usually created via Sync.client(). A store has at most one open client, which it keeps alive (no need to keep a
    reference to it) until the client or the store is closed; see Store.sync_client().
    """

    def __init__(self, store: Store, server_urls: typing.List[str],
                 filter_variables: typing.Optional[typing.Dict[str, str]] = None):
        """Creates a Sync client associated with the given store and options.

        This does not initiate any connection attempts yet: call start() to do so.

        Args:
            store: The ObjectBox store to sync.
            server_urls: List of server URLs to connect to.
            filter_variables: Optional dictionary of filter variable names to values.

        Raises:
            ValueError: If a sync client is already active (not closed) for the given store.
        """
        # Set first, so close() (e.g. via __del__) works if this constructor raises
        self.__c_sync_client_ptr = None
        self.__close_lock = threading.Lock()
        self.__on_store_close = None
        # All ctypes callbacks passed to C: the C client may call them until it is closed, also replaced ones
        # (e.g. while a listener is replaced, the client's thread may be calling the previous one), so keep them all.
        self.__c_callbacks = []
        if not server_urls:
            raise ValueError("Provide at least one server URL")

        if not Sync.is_available():
            raise RuntimeError(
                'Sync is not available in the loaded ObjectBox runtime library. '
                'Install ObjectBox with the Sync variant of the library via "pip install objectbox-sync" '
                '(instead of objectbox); '
                'please visit https://objectbox.io/sync/ for options.')

        self.__store = store

        if not store._c_store:
            raise ValueError("Store is closed")
        if store._sync_client is not None:
            raise ValueError("Only one sync client can be active for a store")

        # Like Java and Dart, create the client via options (allows further options, e.g. flags)
        c_options = c.obx_sync_opt(store._c_store)
        try:
            for url in server_urls:
                c.obx_sync_opt_add_url(c_options, url.encode('utf-8'))
        except BaseException:
            c.obx_sync_opt_free(c_options)  # Only if not passed to obx_sync_create(), which frees them in any case
            raise
        self.__c_sync_client_ptr = c.obx_sync_create(c_options)

        # Close this client when the store is closed (the C API requires the client to be closed first).
        # Like in Java and Dart, the store keeps the client alive until it is closed, so the caller does not have to
        # keep a reference (a store and its client that are both no longer referenced are closed by the cyclic GC).
        self.__on_store_close = self.close
        self.__store._add_close_listener(self.__on_store_close)
        store._sync_client = self

        try:
            for name, value in (filter_variables or {}).items():
                self.put_filter_variable(name, value)
        except BaseException:
            self.close()  # Not reachable by the caller, so close it now (it would block a new client for the store)
            raise

    def __del__(self):
        # Close the SyncClient when this instance is destructed, e.g. garbage collected together with its store
        self.close()

    def __check_sync_ptr_not_null(self):
        if self.__c_sync_client_ptr is None:
            raise ValueError('SyncClient already closed')

    def set_credentials(self, credentials: typing.Union[SyncCredentials, typing.List[SyncCredentials]]):
        """Configure authentication credentials, depending on your server config.

        Any credentials set before are replaced. Usually, credentials are passed to Sync.client(), but this can be used
        to update them later, e.g. when a token expires.

        Args:
            credentials: The credentials to use for authentication; a list to pass multiple credentials (the server
                accepts the client if any of them is valid), which must not include SyncCredentials.none().

        Raises:
            ValueError: If the list is empty or contains SyncCredentials.none() (along with other credentials).
            TypeError: If credentials were not created by the SyncCredentials factory methods.
        """
        self.__check_sync_ptr_not_null()
        credentials_list = list(credentials) if isinstance(credentials, (list, tuple)) else [credentials]
        if len(credentials_list) == 0:
            raise ValueError("Provide at least one credential")
        # Check all before adding any, as the C client would be left with an incomplete set of credentials
        for creds in credentials_list:
            if not isinstance(creds, (SyncCredentialsNone, SyncCredentialsUserPassword, SyncCredentialsSecret)):
                raise TypeError(f"Unsupported credentials: {creds!r}; use the SyncCredentials factory methods")
            if isinstance(creds, SyncCredentialsNone) and len(credentials_list) > 1:
                raise ValueError("SyncCredentials.none() is not supported with multiple credentials")

        if len(credentials_list) == 1:
            creds = credentials_list[0]
            if isinstance(creds, SyncCredentialsNone):
                c.obx_sync_credentials(self.__c_sync_client_ptr, creds.type, None, 0)
            elif isinstance(creds, SyncCredentialsUserPassword):
                c.obx_sync_credentials_user_password(self.__c_sync_client_ptr, creds.type,
                                                     creds.username.encode('utf-8'), creds.password.encode('utf-8'))
            else:
                c.obx_sync_credentials(self.__c_sync_client_ptr, creds.type, creds.secret, len(creds.secret))
            return

        for i, creds in enumerate(credentials_list):
            is_last = (i == len(credentials_list) - 1)
            if isinstance(creds, SyncCredentialsUserPassword):
                c.obx_sync_credentials_add_user_password(self.__c_sync_client_ptr, creds.type,
                                                         creds.username.encode('utf-8'),
                                                         creds.password.encode('utf-8'), is_last)
            else:
                c.obx_sync_credentials_add(self.__c_sync_client_ptr, creds.type, creds.secret, len(creds.secret),
                                           is_last)

    def set_request_updates_mode(self, mode: SyncRequestUpdatesMode):
        """Configures how sync updates are received from the server.

        If automatic updates are turned off, they will need to be requested manually.
        Must be called before start().

        Args:
            mode: The request updates mode to use.

        Raises:
            ValueError: If mode is not a SyncRequestUpdatesMode value.
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_request_updates_mode(self.__c_sync_client_ptr, SyncRequestUpdatesMode(mode))

    def state(self) -> SyncState:
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
        return c.obx_sync_trigger_reconnect(self.__c_sync_client_ptr)

    def request_updates(self, subscribe_for_future_pushes: bool) -> bool:
        """Request updates since we last synchronized our database.

        Additionally, you can subscribe for future pushes from the server, to let
        it send us future updates as they come in.
        Call cancel_updates() to stop the updates.

        Args:
            subscribe_for_future_pushes: If True, also subscribe for future pushes.

        Returns:
            True if the request was likely sent (e.g. the client is logged in); False if it was not sent
            (and will not be sent in the future).
        """
        self.__check_sync_ptr_not_null()
        return c.obx_sync_updates_request(self.__c_sync_client_ptr, subscribe_for_future_pushes)

    def cancel_updates(self) -> bool:
        """Cancel updates from the server so that it will stop sending updates.

        See also request_updates().

        Returns:
            True if the cancellation was likely sent (e.g. the client is logged in); False if it was not sent
            (and will not be sent in the future).
        """
        self.__check_sync_ptr_not_null()
        return c.obx_sync_updates_cancel(self.__c_sync_client_ptr)

    @staticmethod
    def protocol_version() -> int:
        """Returns the protocol version this client uses."""
        return c.obx_sync_protocol_version()

    def protocol_version_server(self) -> int:
        """Returns the protocol version of the server after a connection is
        established (or attempted), zero otherwise.
        """
        self.__check_sync_ptr_not_null()
        return c.obx_sync_protocol_version_server(self.__c_sync_client_ptr)

    def close(self):
        """Closes and cleans up all resources used by this sync client.

        It can no longer be used afterwards, make a new sync client instead.
        Does nothing if this sync client has already been closed.
        Also called when the store is closed. Note: the store keeps its client alive until either is closed.

        Note: do not call this from a listener (it is called by the client's background thread, which this joins),
        and do not use this client concurrently from other threads while closing.
        """
        with self.__close_lock:  # Only one thread may close, e.g. the user and the store (its close listener)
            c_sync_client_ptr = self.__c_sync_client_ptr
            if c_sync_client_ptr is None:
                return
            self.__c_sync_client_ptr = None
        self.__store._remove_close_listener(self.__on_store_close)
        if self.__store._sync_client is self:
            self.__store._sync_client = None
        # Stops the client and joins its background thread; thus, no listener is called after this returns
        c.obx_sync_close(c_sync_client_ptr)
        # Now the C callbacks are no longer used and can be released
        self.__c_callbacks = []

    def is_closed(self) -> bool:
        """Returns if this sync client is closed and can no longer be used."""
        return self.__c_sync_client_ptr is None

    def __c_callback(self, c_callback_type, callback: typing.Optional[typing.Callable]):
        """Returns a C callback for the given Python function (keeps it referenced), or a NULL one if None."""
        if callback is None:
            return c_callback_type()  # NULL function pointer (ctypes does not accept None for a CFUNCTYPE argument)
        c_callback = c_callback_type(callback)
        self.__c_callbacks.append(c_callback)
        return c_callback

    def set_login_listener(self, login_listener: typing.Optional[SyncLoginListener]):
        """Sets a listener to observe login events (success/failure), replacing a previously set one.

        Args:
            login_listener: The listener to receive login events; None to remove the listener.
        """
        self.__check_sync_ptr_not_null()
        c_login_listener = self.__c_callback(
            c.OBX_sync_listener_login_t,
            None if login_listener is None else (lambda arg: login_listener.on_logged_in()))
        c_login_failure_listener = self.__c_callback(
            c.OBX_sync_listener_login_failure_t,
            None if login_listener is None else (lambda arg, sync_login_code: login_listener.on_login_failed(
                _to_sync_code(sync_login_code))))
        c.obx_sync_listener_login(self.__c_sync_client_ptr, c_login_listener, None)
        c.obx_sync_listener_login_failure(self.__c_sync_client_ptr, c_login_failure_listener, None)

    def set_connection_listener(self, connection_listener: typing.Optional[SyncConnectionListener]):
        """Sets a listener to observe connection state changes (connect/disconnect), replacing a previously set one.

        Args:
            connection_listener: The listener to receive connection events; None to remove the listener.
        """
        self.__check_sync_ptr_not_null()
        c_connect_listener = self.__c_callback(
            c.OBX_sync_listener_connect_t,
            None if connection_listener is None else (lambda arg: connection_listener.on_connected()))
        c_disconnect_listener = self.__c_callback(
            c.OBX_sync_listener_disconnect_t,
            None if connection_listener is None else (lambda arg: connection_listener.on_disconnected()))
        c.obx_sync_listener_connect(self.__c_sync_client_ptr, c_connect_listener, None)
        c.obx_sync_listener_disconnect(self.__c_sync_client_ptr, c_disconnect_listener, None)

    def set_completed_listener(self, completed_listener: typing.Optional[SyncCompletedListener]):
        """Sets a listener to observe when synchronization has completed, replacing a previously set one.

        Args:
            completed_listener: The listener to receive "updates completed" events; None to remove the listener.
        """
        self.__check_sync_ptr_not_null()
        c_complete_listener = self.__c_callback(
            c.OBX_sync_listener_complete_t,
            None if completed_listener is None else (lambda arg: completed_listener.on_updates_completed()))
        c.obx_sync_listener_complete(self.__c_sync_client_ptr, c_complete_listener, None)

    def set_change_listener(self, change_listener: typing.Optional[SyncChangeListener]):
        """Sets a listener to observe incoming data changes from the server, replacing a previously set one.

        Args:
            change_listener: The listener to receive change events; None to remove the listener.
        """
        self.__check_sync_ptr_not_null()

        def c_change_callback(arg, sync_change_array_ptr):
            sync_change_array = ctypes.cast(sync_change_array_ptr, ctypes.POINTER(OBX_sync_change_array)).contents
            changes: typing.List[SyncChange] = []
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

        c_change_listener = self.__c_callback(c.OBX_sync_listener_change_t,
                                              None if change_listener is None else c_change_callback)
        c.obx_sync_listener_change(self.__c_sync_client_ptr, c_change_listener, None)

    def wait_for_logged_in_state(self, timeout_millis: int) -> bool:
        """Waits for the sync client to reach the logged-in state.

        Args:
            timeout_millis: Maximum time to wait in milliseconds (must be greater than 0).

        Returns:
            True if the logged-in state was reached within the given timeout; False if the timeout was reached or
            a state was reached that is unlikely to result in a successful login (e.g. disconnected).
        """
        self.__check_sync_ptr_not_null()
        return c.obx_sync_wait_for_logged_in_state(self.__c_sync_client_ptr, timeout_millis)

    def put_filter_variable(self, name: str, value: str):
        """Adds or replaces a Sync filter variable value for the given name.

        Eventually, existing values for the same name are replaced.

        Sync client filter variables can be used in server-side Sync filters to
        filter out objects that do not match the filters. Variables put before login (e.g. before start()) are used
        for the login; changes after login are pending until apply_filter_variables() is called. This allows to put or
        remove multiple variables before applying all changes.

        See also remove_filter_variable(), remove_all_filter_variables() and apply_filter_variables().

        Args:
            name: The name of the filter variable.
            value: The value of the filter variable.
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_filter_variables_put(self.__c_sync_client_ptr, name.encode('utf-8'), value.encode('utf-8'))

    def remove_filter_variable(self, name: str):
        """Removes a previously added Sync filter variable value.

        Note: if the client is already logged in, this change is not applied until apply_filter_variables() is called
        (see put_filter_variable() for details).

        See also put_filter_variable(), remove_all_filter_variables() and apply_filter_variables().

        Args:
            name: The name of the filter variable to remove.
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_filter_variables_remove(self.__c_sync_client_ptr, name.encode('utf-8'))

    def remove_all_filter_variables(self):
        """Removes all previously added Sync filter variable values.

        Note: if the client is already logged in, this change is not applied until apply_filter_variables() is called
        (see put_filter_variable() for details).

        See also put_filter_variable(), remove_filter_variable() and apply_filter_variables().
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_filter_variables_remove_all(self.__c_sync_client_ptr)

    def apply_filter_variables(self):
        """Applies all pending filter variable changes (put or removed after login).

        If the client is connected, sends the updated variables to the server: the client then reconnects and the
        server brings the client's data in line with the new variables. If the client is not connected, the updated
        variables are used with the next login.

        See also put_filter_variable(), remove_filter_variable() and remove_all_filter_variables().
        """
        self.__check_sync_ptr_not_null()
        c.obx_sync_filter_variables_apply(self.__c_sync_client_ptr)

    def outgoing_message_count(self, limit: int = 0) -> int:
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

    @staticmethod
    def is_available() -> bool:
        """Returns True if the loaded ObjectBox native library supports Sync."""
        return c.obx_has_feature(c.Feature.Sync)

    @staticmethod
    def client(
            store: Store,
            server_url: typing.Union[str, typing.List[str]],
            credentials: typing.Union[SyncCredentials, typing.List[SyncCredentials]],
            filter_variables: typing.Optional[typing.Dict[str, str]] = None
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
            server_url: The URL of the Sync server to connect to, e.g. "ws://127.0.0.1:9999" ("wss://" for an encrypted
                connection); or a list of URLs to work with multiple servers (a random URL is selected for each
                connection attempt).
            credentials: The credentials to use for authentication; or a list of credentials (see
                SyncClient.set_credentials()).
            filter_variables: Optional dictionary of filter variable names to values.

        Returns:
            A configured SyncClient instance.
        """
        server_urls = [server_url] if isinstance(server_url, str) else list(server_url)
        client = SyncClient(store, server_urls, filter_variables)
        try:
            client.set_credentials(credentials)
        except BaseException:
            client.close()
            raise
        return client
