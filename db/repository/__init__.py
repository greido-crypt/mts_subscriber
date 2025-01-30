from .keys_repo import KeysRepository
from .users_repo import UsersRepository
from .accounts_repo import AccountsRepository
from .cookies_repo import CookiesRepository
from .invites_repo import InvitesRepository

invites_repository = InvitesRepository()
users_repository = UsersRepository()
keys_repository = KeysRepository()
accounts_repository = AccountsRepository()
cookies_repository = CookiesRepository()

__all__ = ['users_repository',
           'keys_repository',
           'accounts_repository',
           'cookies_repository',
           'invites_repository']
