from django.utils.http import url_has_allowed_host_and_scheme


def safe_next(request, default="/"):
    """Return the POSTed/GET `next` URL only if it points back at this site."""
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return default
