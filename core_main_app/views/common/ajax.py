"""
    Common ajax
"""
import json

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.generic.edit import UpdateView, CreateView, DeleteView

from core_main_app.commons import exceptions
from core_main_app.components.template import api as template_api
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.components.template_version_manager.models import TemplateVersionManager
from core_main_app.components.version_manager import api as version_manager_api
from core_main_app.views.admin.forms import EditTemplateForm


class AddObjectModalView(CreateView):
    """ Common AddObjectModalView.
        Should be used with add.html and add.js.
    """
    template_name = 'core_main_app/common/commons/form.html'
    form_class = None
    model = None
    success_url = None
    success_message = None

    def form_invalid(self, form):
        # Get initial response
        response = super(AddObjectModalView, self).form_invalid(form)
        data = {
            'is_valid': False,
            'responseText': response.rendered_content
        }
        return JsonResponse(data)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # Call private save method
        # Populate self.object without committing to the database
        self.object = form.save(commit=False)
        self._save(form)
        if form.is_valid():
            data = {
                'is_valid': True,
                'url': self.get_success_url(),
            }

            if self.success_message:
                messages.success(self.request, self.success_message)

            return JsonResponse(data)
        else:
            return self.form_invalid(form)

    def _save(self, form):
        # Save treatment.
        super(AddObjectModalView, self).form_valid(form)

    @staticmethod
    def get_modal_html_path():
        return "core_main_app/common/modals/add_page_modal.html"

    @staticmethod
    def get_modal_js_path():
        return {"path": 'core_main_app/common/js/modals/add.js', "is_raw": False}


class EditObjectModalView(UpdateView):
    """ Common EditObjectModalView.
        Should be used with edit_page_modal.html and edit.js.
    """
    template_name = 'core_main_app/common/commons/form.html'
    form_class = None
    model = None
    success_url = None
    success_message = None

    def form_invalid(self, form):
        # Get initial response
        response = super(EditObjectModalView, self).form_invalid(form)
        data = {
            'is_valid': False,
            'responseText': response.rendered_content
        }
        return JsonResponse(data)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # Call private save method
        self._save(form)
        if form.is_valid():
            data = {
                'is_valid': True,
                'url': self.get_success_url(),
            }

            if self.success_message:
                messages.success(self.request, self.success_message)

            return JsonResponse(data)
        else:
            return self.form_invalid(form)

    def _save(self, form):
        # Save treatment.
        super(EditObjectModalView, self).form_valid(form)

    @staticmethod
    def get_modal_html_path():
        return "core_main_app/common/modals/edit_page_modal.html"

    @staticmethod
    def get_modal_js_path():
        return {"path": 'core_main_app/common/js/modals/edit.js', "is_raw": False}


class DeleteObjectModalView(DeleteView):
    """ Common DeleteObjectModalView.
        Should be used with delete_page_modal.html and delete.js.
    """
    template_name = 'core_main_app/common/commons/form_delete.html'
    model = None
    field_for_name = None
    success_url = None
    success_message = None

    def delete(self, request, *args, **kwargs):
        """
        Delete method.
        """
        try:
            self.object = self.get_object()
            self._delete(request, *args, **kwargs)

            if self.success_message:
                messages.success(self.request, self.success_message)
        except Exception, e:
            messages.error(self.request, e.message)

        data = {'url': self.get_success_url()}
        return JsonResponse(data)

    def _delete(self, request, *args, **kwargs):
        """
        Delete treatment.
        """
        # Delete treatment.
        super(DeleteObjectModalView, self).delete(request, *args, **kwargs)

    def _get_object_name(self):
        """
        Get object name
        """
        object_name = ''
        if self.object:
            if self.field_for_name:
                object_name = getattr(self.object, self.field_for_name, str(self.object))
            else:
                object_name = str(self.object)

        return object_name

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(DeleteObjectModalView, self).get_context_data(**kwargs)
        # Add the object representation
        context['object_name'] = self._get_object_name()

        return context

    @staticmethod
    def get_modal_html_path():
        return "core_main_app/common/modals/delete_page_modal.html"

    @staticmethod
    def get_modal_js_path():
        return {"path": 'core_main_app/common/js/modals/delete.js', "is_raw": False}


class EditTemplateVersionManagerView(EditObjectModalView):
    form_class = EditTemplateForm
    model = TemplateVersionManager
    success_url = reverse_lazy("admin:core_main_app_templates")
    success_message = 'Name edited with success.'

    def _save(self, form):
        # Save treatment.
        try:
            template_version_manager_api.edit_title(self.object, form.cleaned_data.get('title'))
        except exceptions.NotUniqueError:
            form.add_error(None, "An object with the same name already exists. Please choose "
                                 "another name.")
        except Exception, e:
            form.add_error(None, e.message)


def disable_version_manager(request):
    """Disable a version manager.

    Args:
        request:

    Returns:

    """
    try:
        version_manager = version_manager_api.get(request.GET['id'])
        version_manager_api.disable(version_manager)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def restore_version_manager(request):
    """Restore a disabled version manager.

    Args:
        request:

    Returns:

    """
    try:
        version_manager = version_manager_api.get(request.GET['id'])
        version_manager_api.restore(version_manager)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def disable_template_version_from_version_manager(request):
    """ Disable a template version of a version manager.

    Args:
        request:

    Returns:

    """
    try:
        disable_version_of_version_manager(template_api.get(request.GET['id']))
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def disable_version_of_version_manager(version):
    """ Disable a version of a version manager.

    Args:
        version:

    Returns:

    """
    try:
        version_manager_api.disable_version(version)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')


def restore_template_version_from_version_manager(request):
    """ Restore a disabled template version of a version manager.

    Args:
        request:

    Returns:

    """
    try:
        restore_version_from_version_manager(template_api.get(request.GET['id']))
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def restore_version_from_version_manager(version):
    """ Restore a disabled version of a version manager.

    Args:
        version:

    Returns:

    """
    try:
        version_manager_api.restore_version(version)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')


def set_current_template_version_from_version_manager(request):
    """ Set the current version of a template.

    Args:
        request:

    Returns:

    """
    try:
        set_current_version_from_version_manager(template_api.get(request.GET['id']))
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def set_current_version_from_version_manager(version):
    """ Set the current version of a version manager.

    Args:
        version:

    Returns:

    """
    try:
        version_manager_api.set_current(version)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

