from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import login as login_view
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import (View, ListView, DetailView, UpdateView,
        CreateView, DeleteView, FormView)

from accounts.models import Account
from accounts.mixins import (AccountMixin, AccountUserMixin,
        MembershipRequiredMixin, AdminRequiredMixin, OwnerRequiredMixin)
from accounts.forms import (LoginForm, AccountForm, AccountUserForm,
        AccountUserAddForm, AccountAddForm, UserProfileForm)


class LoginView(FormView):
    """
    Performs the same actions as the default Django login view but also
    checks for a logged in user and redirects that person if s/he is
    logged in.
    """
    template_name = "accounts/login.html"
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        redirect_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
        if request.user.is_authenticated():
            return HttpResponseRedirect(redirect_url)
        else:
            form = LoginForm(initial={"redirect_url": redirect_url})
            return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        return login_view(request, redirect_field_name="redirect_url",
                authentication_form=LoginForm)


class LogoutView(View):
    """
    Logs the user out, and then redirects to the login view. It also
    updates the request messages with a message that the user has 
    successfully logged out.
    """

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.INFO, "You have successfully logged out.")
        return HttpResponseRedirect(reverse('login'))

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class BaseAccountList(ListView):
    model = Account
    context_object_name = "accounts"


class BaseAccountDetail(AccountMixin, DetailView):
    def get_context_data(self, **kwargs):
        context = super(BaseAccountDetail, self).get_context_data(**kwargs)
        context['account_users'] = self.account.account_users.all()
        context['account'] = self.account
        return context


class BaseAccountCreate(View):
    form_class = AccountAddForm
    template_name = 'accounts/account_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        return super(BaseAccountCreate, self).form_valid(form)


class BaseAccountUpdate(AccountMixin, UpdateView):
    form_class = AccountForm


class BaseAccountDelete(AccountMixin, DeleteView):
    def get_success_url(self):
        return reverse("account_list")


class BaseAccountUserList(AccountMixin, ListView):
    def get(self, request, *args, **kwargs):
        self.account = self.get_account(**kwargs)
        self.object_list = self.account.account_users.all()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(account_users=self.object_list,
                account=self.account)
        return self.render_to_response(context)


class BaseAccountUserDetail(AccountUserMixin, DetailView):
    pass


class BaseAccountUserCreate(AccountMixin, CreateView):
    form_class = AccountUserAddForm
    template_name = 'accounts/accountuser_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(BaseAccountUserCreate, self).get_form_kwargs()
        kwargs.update({'account': self.account})
        return kwargs

    def get(self, request, *args, **kwargs):
        self.account = self.get_object()
        return super(BaseAccountUserCreate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.account = self.get_object()
        return super(BaseAccountUserCreate, self).post(request, *args, **kwargs)


class BaseAccountUserUpdate(AccountUserMixin, UpdateView):
    form_class = AccountUserForm


class BaseAccountUserDelete(AccountUserMixin, DeleteView):
    def get_success_url(self):
        return reverse("accountuser_list")


class AccountList(BaseAccountList):
    pass


class AccountCreate(BaseAccountCreate):
    pass


class AccountDetail(MembershipRequiredMixin, BaseAccountDetail):
    pass


class AccountUpdate(AdminRequiredMixin, BaseAccountUpdate):
    pass


class AccountDelete(OwnerRequiredMixin, BaseAccountDelete):
    pass


class AccountUserList(MembershipRequiredMixin, BaseAccountUserList):
    pass


class AccountUserDetail(AdminRequiredMixin, BaseAccountUserDetail):
    pass


class AccountUserUpdate(AdminRequiredMixin, BaseAccountUserUpdate):
    pass


class AccountUserCreate(AdminRequiredMixin, BaseAccountUserCreate):
    pass


class AccountUserDelete(AdminRequiredMixin, BaseAccountUserDelete):
    pass


class UserProfileView(UpdateView):
    form_class = UserProfileForm
    template_name = "accounts/accountuser_form.html"

    def get_success_url(self):
        success_url = getattr(self, 'success_url')
        return success_url if success_url else reverse('user_profile')

    def get_object(self, **kwargs):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super(UserProfileView, self).get_form_kwargs()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        context['profile'] = True
        return context
