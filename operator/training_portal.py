import os
import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["training_portal_create", "training_portal_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "trainingportals", id="eduk8s")
def training_portal_create(name, spec, logger, **_):
    apps_api = kubernetes.client.AppsV1Api()
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    extensions_api = kubernetes.client.ExtensionsV1beta1Api()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # Use the name of the custom resource with prefix "eduk8s-" as the
    # name of the portal namespace.

    portal_name = name
    portal_namespace = f"{portal_name}-ui"

    # Determine URL to be used for accessing the portal web interface.

    domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
    domain = spec.get("portal", {}).get("domain", domain)

    portal_hostname = f"{portal_name}-ui.{domain}"

    # Determine password for the portal. Use "eduk8s" if not defined.
    # Also generate an admin password for portal management.

    characters = string.ascii_letters + string.digits

    portal_password = spec.get("portal", {}).get("password", "eduk8s")
    admin_password = "".join(random.sample(characters, 32))

    # Generate a token for use in workshop requests in case needed.

    token = "".join(random.sample(characters, 32))

    # Calculate the capacity. This is the number of attendees who need
    # to perform the workshops. We will need this number of each of the
    # listed workshops. Also generate a list of attendees based on this
    # capacity, with a distinct password for each.

    capacity = int(spec.get("portal", {}).get("capacity", "1"))

    attendees = []

    for n in range(1, capacity + 1):
        session_id = f"user{n}"

        attendees.append(
            {
                "id": session_id,
                "username": session_id,
                "password": "".join(random.sample(characters, 16)),
            }
        )

    # Create the namespace for holding the web interface for the portal.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": portal_namespace},
    }

    # Make the namespace for the portal a child of the custom resource
    # for the training portal. This way the namespace will be
    # automatically deleted when the resource definition for the
    # training portal is deleted and we don't have to clean up anything
    # explicitly.

    kopf.adopt(namespace_body)

    namespace_instance = core_api.create_namespace(body=namespace_body)

    # Delete any limit ranges applied to the namespace so they don't
    # cause issues with deploying the training portal.

    limit_ranges = core_api.list_namespaced_limit_range(namespace=portal_namespace)

    for limit_range in limit_ranges.items:
        core_api.delete_namespaced_limit_range(
            namespace=portal_namespace, name=limit_range["metadata"]["name"]
        )

    # Delete any resource quotas applied to the namespace so they don't
    # cause issues with deploying the training portal.

    resource_quotas = core_api.list_namespaced_resource_quota(
        namespace=portal_namespace
    )

    for resource_quota in resource_quotas.items:
        core_api.delete_namespaced_resource_quota(
            namespace=portal_namespace, name=resource_quota["metadata"]["name"]
        )

    # Now need to loop over the list of the workshops and create the
    # workshop environment and required number of sessions for each.

    environments = []

    for n, workshop in enumerate(spec.get("workshops", [])):
        # Use the name of the custom resource as the name of the workshop
        # environment.

        workshop_name = workshop["name"]
        environment_name = f"{portal_name}-ws{n+1}"

        # Verify that the workshop definition exists.

        try:
            workshop_instance = custom_objects_api.get_cluster_custom_object(
                "training.eduk8s.io", "v1alpha1", "workshops", workshop_name
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise kopf.TemporaryError(f"Workshop {workshop_name} is not available.")

        workshop_details = {
            "name": workshop_name,
            "vendor": workshop_instance.get("spec", {}).get("vendor", ""),
            "title": workshop_instance.get("spec", {}).get("title", ""),
            "description": workshop_instance.get("spec", {}).get("description", ""),
            "url": workshop_instance.get("spec", {}).get("url", ""),
        }

        sessions_list = []

        # Defined the body of the workshop environment to be created.

        env = workshop.get("env", [])

        environment_body = {
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "kind": "WorkshopEnvironment",
            "metadata": {"name": environment_name},
            "spec": {
                "workshop": {"name": workshop_name},
                "request": {"token": token, "namespaces": [environment_name]},
                "session": {"username": "eduk8s", "domain": domain, "env": env,},
                "environment": {"objects": [],},
            },
        }

        # Create a new workshop session for each attendee in the list.
        # We add this to the workshop environment as a resource object
        # to be created later when the workshop environment is created.

        for attendee in attendees:
            session_id = attendee["id"]
            session_name = f"{environment_name}-{session_id}"
            session_hostname = f"{session_name}.{domain}"

            session_body = {
                "apiVersion": "training.eduk8s.io/v1alpha1",
                "kind": "WorkshopSession",
                "metadata": {
                    "name": session_name,
                    "labels": {"workshop-environment": environment_name,},
                },
                "spec": {
                    "environment": {"name": environment_name,},
                    "session": {
                        "id": session_id,
                        "username": session_id,
                        "password": attendee["password"],
                        "hostname": session_hostname,
                        "env": env,
                    },
                },
            }

            environment_body["spec"]["environment"]["objects"].append(session_body)

            sessions_list.append(
                {
                    "id": session_id,
                    "username": session_id,
                    "password": attendee["password"],
                    "hostname": session_hostname,
                }
            )

        # Make the workshop environment a child of the custom resource for
        # the training portal. This way the whole workshop environment will be
        # automatically deleted when the resource definition for the
        # training portal is deleted and we don't have to clean up anything
        # explicitly.

        kopf.adopt(environment_body)

        custom_objects_api.create_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshopenvironments", environment_body,
        )

        environments.append(
            {
                "name": environment_name,
                "workshop": workshop_details,
                "sessions": sessions_list,
            }
        )

    # Deploy the training portal web interface. First up need to create a
    # service account and binding required roles to it.

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": "eduk8s-portal"},
    }

    core_api.create_namespaced_service_account(
        namespace=portal_namespace, body=service_account_body
    )

    role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "Role",
        "metadata": {"name": "eduk8s-portal"},
        "rules": [
            {
                "apiGroups": ["training.eduk8s.io"],
                "resources": ["workshopsessions"],
                "verbs": ["get", "list"],
            }
        ],
    }

    rbac_authorization_api.create_namespaced_role(
        namespace=portal_namespace, body=role_body
    )

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {"name": "eduk8s-portal"},
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "Role",
            "name": "eduk8s-portal",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "eduk8s-portal",
                "namespace": portal_namespace,
            }
        ],
    }

    rbac_authorization_api.create_namespaced_role_binding(
        namespace=portal_namespace, body=role_binding_body
    )

    # Next create the deployment for the portal web interface.

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "eduk8s-portal"},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": "eduk8s-portal"}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {"labels": {"deployment": "eduk8s-portal"}},
                "spec": {
                    "serviceAccountName": "eduk8s-portal",
                    "containers": [
                        {
                            "name": "portal",
                            "image": "quay.io/eduk8s/eduk8s-portal:master",
                            "imagePullPolicy": "Always",
                            "resources": {
                                "requests": {"memory": "256Mi"},
                                "limits": {"memory": "256Mi"},
                            },
                            "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                            "env": [
                                {"name": "ADMIN_PASSWORD", "value": admin_password,},
                                {"name": "PORTAL_PASSWORD", "value": portal_password,},
                                {"name": "WORKSHOP_CAPACITY", "value": str(capacity),},
                            ],
                        }
                    ],
                },
            },
        },
    }

    apps_api.create_namespaced_deployment(
        namespace=portal_namespace, body=deployment_body
    )

    # Finally expose the deployment via a service and ingress route.

    service_body = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "eduk8s-portal"},
        "spec": {
            "type": "ClusterIP",
            "ports": [{"port": 8080, "protocol": "TCP", "targetPort": 8080}],
            "selector": {"deployment": "eduk8s-portal"},
        },
    }

    core_api.create_namespaced_service(namespace=portal_namespace, body=service_body)

    ingress_body = {
        "apiVersion": "extensions/v1beta1",
        "kind": "Ingress",
        "metadata": {"name": "eduk8s-portal"},
        "spec": {
            "rules": [
                {
                    "host": portal_hostname,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "backend": {
                                    "serviceName": "eduk8s-portal",
                                    "servicePort": 8080,
                                },
                            }
                        ]
                    },
                }
            ]
        },
    }

    extensions_api.create_namespaced_ingress(
        namespace=portal_namespace, body=ingress_body
    )

    # Save away the details of the portal which was created in status.

    return {
        "url": f"http://{portal_hostname}",
        "credentials": {"portal": portal_password, "administrator": admin_password},
        "environments": environments,
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "trainingportals", optional=True)
def training_portal_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
