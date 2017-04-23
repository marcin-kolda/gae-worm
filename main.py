import googleapiclient.discovery
from oauth2client.client import GoogleCredentials
from google.appengine.api import app_identity
import json
import base64
import webapp2

from webapp2_extras import jinja2

VERSION = 'v1'


class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        rv = self.jinja2.render_template(_template, version=VERSION, **context)
        self.response.write(rv)


class MainHandler(BaseHandler):
    def get(self):
        self.render_response('index.html')


class ProjectsHandler(BaseHandler):
    def __init__(self, request=None, response=None):
        super(ProjectsHandler, self).__init__(request, response)
        self.cloudresourcemanager = googleapiclient.discovery.build(
            'cloudresourcemanager',
            'v1',
            credentials=GoogleCredentials.get_application_default()
        )

    def get(self):
        self.render_response('projects.html', projects=self._list_projects())

    def _list_projects(self):
        request = self.cloudresourcemanager.projects().list()

        while request is not None:
            response = request.execute()
            if 'projects' in response:
                for project in response['projects']:
                    yield project

            request = self.cloudresourcemanager.projects().list_next(request,
                                                                     response)


class IamHandler(BaseHandler):
    def __init__(self, request=None, response=None):
        super(IamHandler, self).__init__(request, response)
        self.cloudresourcemanager = googleapiclient.discovery.build(
            'cloudresourcemanager',
            'v1',
            credentials=GoogleCredentials.get_application_default()
        )

    def get(self):
        project_id = self.request.get('project',
                                      app_identity.get_application_id())
        response = self.cloudresourcemanager.projects().getIamPolicy(
            resource=project_id, body={}).execute()
        self.render_response('project_iam.html', bindings=response['bindings'],
                             project_id=project_id)


class ServicesHandler(BaseHandler):
    def __init__(self, request=None, response=None):
        super(ServicesHandler, self).__init__(request, response)
        self.servicemanagement = googleapiclient.discovery.build(
            'servicemanagement',
            'v1',
            credentials=GoogleCredentials.get_application_default()
        )

    def get(self):
        project = self.request.get('project', app_identity.get_application_id())
        service = self.request.get('service', None)

        if service:
            response = self.servicemanagement.services().enable(
                serviceName=service,
                body={'consumerId': 'project:' + project}
            ).execute()
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(response))
        else:
            self.render_response('services.html',
                                 services=self._list_services(project),
                                 project_id=project)

    def _list_services(self, project):
        request = self.servicemanagement.services().list(
            consumerId="project:" + project)

        while request is not None:
            response = request.execute()
            if 'services' in response:
                for service in response['services']:
                    yield service

            request = self.servicemanagement.services().list_next(request,
                                                                  response)


class ServiceAccountsHandler(BaseHandler):
    def __init__(self, request=None, response=None):
        super(ServiceAccountsHandler, self).__init__(request, response)
        self.iam_service = googleapiclient.discovery.build(
            'iam', 'v1',
            credentials=GoogleCredentials.get_application_default())

    def get(self):
        project = self.request.get('project', app_identity.get_application_id())
        self.render_response('serviceAccounts.html',
                             accounts=self._list_service_accounts(project),
                             project_id=project)

    def _list_service_accounts(self, project):
        request = self.iam_service.projects().serviceAccounts().list(
            name='projects/' + project)

        while request is not None:
            response = request.execute()
            if 'accounts' in response:
                for account in response['accounts']:
                    yield account

            request = self.iam_service.projects().serviceAccounts().list_next(
                request, response)


class CreateKeysHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        super(CreateKeysHandler, self).__init__(request, response)
        self.iam_service = googleapiclient.discovery.build(
            'iam', 'v1',
            credentials=GoogleCredentials.get_application_default())

    def get(self):
        service_account = self.request.get('serviceAccount')

        response = self.iam_service.projects().serviceAccounts().keys().create(
            name=service_account, body={}).execute()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(
            base64.b64decode(response['privateKeyData']))


class DeployHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        super(DeployHandler, self).__init__(request, response)
        self.appengine = googleapiclient.discovery.build(
            'appengine',
            'v1',
            credentials=GoogleCredentials.get_application_default()
        )

    def get(self):
        project = self.request.get('project')
        service = self.request.get('service', 'gae-worm')
        version = self.request.get('version', VERSION)
        worm_version = self.request.get('wormVersion', VERSION)

        body = {
            "deployment":
                {
                    "zip":
                        {
                            "sourceUrl": "https://storage.googleapis.com/gae-worm/gae-worm-{0}.zip".format(
                                worm_version)
                        }
                },
            "runtime": "python27",
            "threadsafe": True,
            "libraries":
                [
                    {
                        "name": "webapp2",
                        "version": "latest"
                    },
                    {
                        "name": "jinja2",
                        "version": "latest"
                    }
                ],
            "handlers":
                [
                    {
                        "urlRegex": ".*",
                        "script": {"scriptPath": "main.app"}
                    }

                ],
            "id": version
        }

        response = self.appengine.apps().services().versions().create(
            appsId=project, servicesId=service, body=body).execute()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(response))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/projects', ProjectsHandler),
    ('/iam', IamHandler),
    ('/services', ServicesHandler),
    ('/serviceAccounts', ServiceAccountsHandler),
    ('/createKeys', CreateKeysHandler),
    ('/deploy', DeployHandler)
], debug=True)
