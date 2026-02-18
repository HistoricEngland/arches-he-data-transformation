from django.utils.translation import gettext as _


def success_response(data=None, **extra):
    resp = {"success": True}
    if data is not None:
        resp["data"] = data
    if extra:
        resp.update(extra)
    return resp


def error_response(error_msg, title=None):
    """Standardize error response shape used by UI handlers."""
    return {
        "success": False,
        "data": error_msg,
        "title": title or _("Bulk HTML Export Failed"),
        "message": _(error_msg),
    }
