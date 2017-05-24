from django.http.response import HttpResponseRedirect
from django.template import loader
from django.template.context import Context
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.html import escape as html_escape
from django.core.urlresolvers import reverse
from django.views.generic import View
from core_main_app.commons import exceptions
from core_main_app.components.template.models import Template
from core_main_app.components.template_version_manager.models import TemplateVersionManager
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.components.version_manager import api as version_manager_api
from core_main_app.utils.rendering import admin_render
from core_main_app.utils.xml import get_imports_and_includes
from core_main_app.views.admin.forms import UploadTemplateForm, UploadVersionForm, UploadXSLTForm, \
    TemplateXsltRenderingForm
from core_main_app.settings import INSTALLED_APPS
from core_main_app.components.xsl_transformation.models import XslTransformation
from core_main_app.components.xsl_transformation import api as xslt_transformation_api
from core_main_app.components.template_xsl_rendering.models import TemplateXslRendering
from core_main_app.components.template_xsl_rendering import api as template_xsl_rendering_api
from core_main_app.components.template import api as template_api


@staff_member_required
def admin_home(request):
    """

    Args:
        request:

    Returns:

    """
    return admin_render(request,
                        'core_main_app/admin/dashboard.html')


@staff_member_required
def manage_templates(request):
    """View that allows template management

    Args:
        request:

    Returns:

    """
    # get all current templates
    templates = template_version_manager_api.get_global_version_managers()

    context = {
        'object_name': 'Template',
        'available': [template for template in templates if not template.is_disabled],
        'disabled': [template for template in templates if template.is_disabled]
    }

    assets = {
        "js": [
            {
                "path": 'core_main_app/admin/js/templates/list/restore.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/list/modals/edit.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/list/modals/disable.js',
                "is_raw": False
            }
        ]
    }

    modals = [
        "core_main_app/admin/templates/list/modals/edit.html",
        "core_main_app/admin/templates/list/modals/disable.html"
    ]

    return admin_render(request,
                        'core_main_app/admin/templates/list.html',
                        assets=assets,
                        context=context,
                        modals=modals)


@staff_member_required
def manage_template_versions(request, version_manager_id):
    """View that allows template versions management

    Args:
        request:
        version_manager_id:

    Returns:

    """
    # get the version manager
    version_manager = None

    try:
        version_manager = version_manager_api.get(version_manager_id)
    except:
        # TODO: catch good exception, redirect to error page
        pass

    assets = {
        "js": [
            {
                "path": 'core_main_app/admin/js/templates/versions/set_current.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/versions/restore.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/versions/modals/disable.js',
                "is_raw": False
            }
        ]
    }

    modals = [
        "core_main_app/admin/templates/versions/modals/disable.html"
    ]

    # Use categorized version for easier manipulation in template
    versions = version_manager.versions
    categorized_versions = {
        "available": [],
        "disabled": []
    }

    for index, version in enumerate(versions, 1):
        indexed_version = {
            "index": index,
            "object": version
        }

        if version not in version_manager.disabled_versions:
            categorized_versions["available"].append(indexed_version)
        else:
            categorized_versions["disabled"].append(indexed_version)

    version_manager.versions = categorized_versions

    context = {
        'object_name': 'Template',
        "version_manager": version_manager
    }

    # FIXME: make this more dynamic?
    if 'core_parser_app' in INSTALLED_APPS:
        context["core_parser_app_installed"] = True

    return admin_render(request,
                        'core_main_app/admin/templates/versions.html',
                        assets=assets,
                        modals=modals,
                        context=context)


@staff_member_required
def upload_template(request):
    """Upload template

    Args:
        request:

    Returns:

    """
    assets = {
        "js": [
            {
                "path": 'core_main_app/admin/js/templates/upload/dependency_resolver.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/upload/dependencies.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/upload/dependencies.raw.js',
                "is_raw": True
            }
        ]
    }

    context = {
        'object_name': 'Template',
        'url': reverse("admin:core_main_app_upload_template"),
        'redirect_url': reverse("admin:core_main_app_templates")
    }

    # method is POST
    if request.method == 'POST':
        form = UploadTemplateForm(request.POST,  request.FILES)
        context['upload_form'] = form

        if form.is_valid():
            return _save_template(request, assets, context)
        else:
            # Display error from the form
            return _upload_template_response(request, assets, context)
    # method is GET
    else:
        # render the form to upload a template
        context['upload_form'] = UploadTemplateForm()
        return _upload_template_response(request, assets, context)


@staff_member_required
def upload_template_version(request, version_manager_id):
    """Upload template version

    Args:
        request:
        version_manager_id:

    Returns:

    """
    assets = {
        "js": [
            {
                "path": 'core_main_app/admin/js/templates/upload/dependency_resolver.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/upload/dependencies.js',
                "is_raw": False
            },
            {
                "path": 'core_main_app/admin/js/templates/upload/dependencies.raw.js',
                "is_raw": True
            }
        ]
    }

    template_version_manager = version_manager_api.get(version_manager_id)
    context = {
        'object_name': "Template",
        'version_manager': template_version_manager,
        'url': reverse("admin:core_main_app_upload_template_version",
                       kwargs={'version_manager_id': template_version_manager.id}),
        'redirect_url': reverse("admin:core_main_app_manage_template_versions",
                                kwargs={'version_manager_id': template_version_manager.id})
    }

    # method is POST
    if request.method == 'POST':
        form = UploadVersionForm(request.POST,  request.FILES)
        context['upload_form'] = form

        if form.is_valid():
            return _save_template_version(request, assets, context, template_version_manager)
        else:
            # Display errors from the form
            return _upload_template_response(request, assets, context)
    # method is GET
    else:
        # render the form to upload a template
        context['upload_form'] = UploadVersionForm()
        return _upload_template_response(request, assets, context)


def _save_template(request, assets, context):
    """Saves a template

    Args:
        request:
        assets:
        context:

    Returns:

    """
    # get the schema name
    name = request.POST['name']
    # get the file from the form
    xsd_file = request.FILES['upload_file']
    # read the content of the file
    xsd_data = _read_xsd_file(xsd_file)

    try:
        template = Template(filename=xsd_file.name, content=xsd_data)
        template_version_manager = TemplateVersionManager(title=name)
        template_version_manager_api.insert(template_version_manager, template)
        return HttpResponseRedirect(reverse("admin:core_main_app_templates"))
    except exceptions.XSDError, xsd_error:
        return _handle_xsd_errors(request, assets, context, xsd_error, xsd_data, xsd_file.name)
    except Exception, e:
        context['errors'] = html_escape(e.message)
        return _upload_template_response(request, assets, context)


def _save_template_version(request, assets, context, template_version_manager):
    """Saves a template version

    Args:
        request:
        assets:
        context:
        template_version_manager:

    Returns:

    """
    # get the file from the form
    xsd_file = request.FILES['xsd_file']
    # read the content of the file
    xsd_data = _read_xsd_file(xsd_file)

    try:
        template = Template(filename=xsd_file.name, content=xsd_data)
        template_version_manager_api.insert(template_version_manager, template)
        return HttpResponseRedirect(reverse("admin:core_main_app_manage_template_versions",
                                            kwargs={'version_manager_id': str(template_version_manager.id)}))
    except exceptions.XSDError, xsd_error:
        return _handle_xsd_errors(request, assets, context, xsd_error, xsd_data, xsd_file.name)
    except Exception, e:
        context['errors'] = html_escape(e.message)
        return _upload_template_response(request, assets, context)


def _handle_xsd_errors(request, assets, context, xsd_error, xsd_content, filename):
    """Handles XSD errors. Builds dependency resolver if needed.

    Args:
        request:
        context:
        xsd_error:
        xsd_content:
        filename:

    Returns:

    """
    imports, includes = get_imports_and_includes(xsd_content)
    # a problem with includes/imports has been detected
    if len(includes) > 0 or len(imports) > 0:
        # build dependency resolver
        context['dependency_resolver'] = _get_dependency_resolver_html(imports, includes, xsd_content,
                                                                       filename)
        return _upload_template_response(request, assets, context)
    else:
        context['errors'] = html_escape(xsd_error.message)
        return _upload_template_response(request, assets, context)


def _read_xsd_file(xsd_file):
    """Returns the content of the file uploaded using Django FileField

    Returns:

    """
    # put the cursor at the beginning of the file
    xsd_file.seek(0)
    # read the content of the file
    return xsd_file.read()


def _upload_template_response(request, assets, context):
    """Renders template upload response

    Args:
        request:
        context:

    Returns:

    """
    return admin_render(request,
                        'core_main_app/admin/templates/upload.html',
                        assets=assets,
                        context=context)


def _get_dependency_resolver_html(imports, includes, xsd_data, filename):
    """
    Return HTML for dependency resolver form
    :param imports:
    :param includes:
    :param xsd_data:
    :return:
    """
    # build the list of dependencies
    current_templates = template_version_manager_api.get_global_version_managers(_cls=False)
    list_dependencies_template = loader.get_template('core_main_app/admin/list_dependencies.html')
    context = Context({
        'templates': [template for template in current_templates if not template.is_disabled],
    })
    list_dependencies_html = list_dependencies_template.render(context)

    # build the dependency resolver form
    dependency_resolver_template = loader.get_template('core_main_app/admin/dependency_resolver.html')
    context = Context({
        'imports': imports,
        'includes': includes,
        'xsd_content': html_escape(xsd_data),
        'filename': filename,
        'dependencies': list_dependencies_html,
    })
    return dependency_resolver_template.render(context)


class XSLTView(View):
    """
    Class' purpose: XSLT view.
    """

    @staticmethod
    def get(request, *args, **kwargs):
        modals = [
            "core_main_app/admin/xslt/list/modals/edit.html",
            "core_main_app/admin/xslt/list/modals/delete.html"
        ]

        assets = {
            "js": [
                {
                    "path": "core_main_app/admin/js/xslt/list/modals/edit.js",
                    "is_raw": False
                },
                {
                    "path": "core_main_app/admin/js/xslt/list/modals/delete.js",
                    "is_raw": False
                }
            ],
        }

        context = {
            'object_name': 'XSLT',
            "xslt": xslt_transformation_api.get_all(),
            "update_url": reverse('admin:core_main_app_upload_xslt')
        }

        return admin_render(request, "core_main_app/admin/xslt/list.html", modals=modals, assets=assets,
                            context=context)


class UploadXSLTView(View):
    """
    Class' purpose: Upload XSLT view.
    """
    form_class = UploadXSLTForm
    template_name = 'core_main_app/admin/xslt/upload.html'
    object_name = 'XSLT'

    def __init__(self, **kwargs):
        super(UploadXSLTView, self).__init__(**kwargs)
        self.context = {}
        self.context.update({'object_name': self.object_name})

    def get(self, request, *args, **kwargs):
        self.context.update({'upload_form': self.form_class()})
        return admin_render(request, self.template_name, context=self.context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        self.context.update({'upload_form': form})

        if form.is_valid():
            return self._save_xslt(request)
        else:
            # Display error from the form
            return admin_render(request, self.template_name, context=self.context)

    def _save_xslt(self, request):
        """Saves an XSLT.

        Args:
            request: Request.

        """
        try:
            # get the XSLT name
            name = request.POST['name']
            # get the file from the form
            xsd_file = request.FILES['upload_file']
            # read the content of the file
            xsd_data = _read_xsd_file(xsd_file)
            xslt = XslTransformation(name=name, filename=xsd_file.name, content=xsd_data)
            xslt_transformation_api.upsert(xslt)

            return HttpResponseRedirect(reverse("admin:core_main_app_xslt"))
        except Exception, e:
            self.context.update({'errors': html_escape(e.message)})
            return admin_render(request, 'core_main_app/admin/xslt/upload.html', context=self.context)


class TemplateXSLRenderingView(View):
    """
    Class' purpose: Template XSL rendering view.
    """
    form_class = TemplateXsltRenderingForm
    template_name = "core_main_app/admin/templates_xslt/main.html"
    context = {}

    def get(self, request, *args, **kwargs):
        """ GET request. Creates/Shows the form for the configuration.

        Args:
            request:
            *args:
            **kwargs:

        Returns:

        """
        template_id = kwargs.pop('template_id')
        # Get the template
        template = template_api.get(template_id)
        try:
            # Get the existing configuration to build the form
            template_xsl_rendering = template_xsl_rendering_api.get_by_template_id(template_id)
            data = {'id': template_xsl_rendering.id, 'template': template.id,
                    'list_xslt': template_xsl_rendering.list_xslt.id if template_xsl_rendering.list_xslt else None,
                    'detail_xslt': template_xsl_rendering.detail_xslt.id if template_xsl_rendering.detail_xslt else None
                   }
        except (Exception, exceptions.DoesNotExist):
            # If no configuration, new form with pre-selected fields.
            data = {'template': template.id, 'list_xslt': None, 'detail_xslt': None}

        self.context = {
            'template_title': template.display_name,
            "form_template_xsl_rendering": self.form_class(data)
        }

        return admin_render(request, self.template_name, context=self.context)

    def post(self, request, *args, **kwargs):
        """ POST request. Try to saves the configuration.

        Args:
            request:
            *args:
            **kwargs:

        Returns:

        """
        form = self.form_class(request.POST, request.FILES)
        self.context.update({'form_template_xsl_rendering': form})

        if form.is_valid():
            return self._save_template_xslt(request)
        else:
            # Display error from the form
            return admin_render(request, self.template_name, context=self.context)

    def _save_template_xslt(self, request):
        """Saves a template xslt rendering.

        Args:
            request: Request.

        """
        try:
            # Get the list xslt instance
            try:
                list_xslt = xslt_transformation_api.get_by_id(request.POST.get('list_xslt'))
            except (Exception, exceptions.DoesNotExist):
                list_xslt = None
            # Get the detail xslt instance
            try:
                detail_xslt = xslt_transformation_api.get_by_id(request.POST.get('detail_xslt'))
            except (Exception, exceptions.DoesNotExist):
                detail_xslt = None

            template_xsl_rendering_api.add_or_delete(template_xsl_rendering_id=request.POST.get('id'),
                                                     template_id=request.POST.get('template'),
                                                     list_xslt=list_xslt, detail_xslt=detail_xslt)

            return HttpResponseRedirect(reverse("admin:core_main_app_templates"))
        except Exception, e:
            self.context.update({'errors': html_escape(e.message)})
            return admin_render(request, self.template_name, context=self.context)
