import csv
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
from urllib import request
import uuid
from arches.app.models import models
import arches.app.models.resource as Resource
from arches.app.models.system_settings import settings
import arches.app.tasks as tasks
import arches_he_data_transformation.tasks as proj_tasks
from arches.app.etl_modules.decorators import load_data_async
from django.db import connection
import os
import json
import logging
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import arches.app.utils.zip as zip_utils

from django.utils.translation import get_language, gettext as _
from arches_he_data_transformation.utils.responses import (
    success_response,
    error_response,
)
from arches.app.etl_modules.base_data_editor import BaseBulkEditor

details = {
    "etlmoduleid": "204e515a-a782-49e6-be98-6134e144468b",
    "name": "Bulk Resource Deleter",
    "description": "ETL module for deleting multiple resources from Arches.",
    "etl_type": "edit",
    "component": "views/components/etl_modules/bulk-resource-deleter",
    "componentname": "bulk-resource-deleter",
    "modulename": "bulk_resource_deleter.py",
    "classname": "BulkResourceDeleter",
    "config": {"bgColor": "#f5c60a", "circleColor": "#f9dd6c"},
    "icon": "fa fa-upload",
    "slug": "bulk-resource-deleter",
    "helpsortorder": 9,
    "helptemplate": "bulk-resource-deleter-help",
}


class BulkResourceDeleter(BaseBulkEditor):

    def __init__(self, request=None, loadid=None, transactionid=None, params=None):
        self.request = request
        self.user = request.user if request else None
        self.userid = request.user.id if request else None
        self.useremail = request.user.email if request else None
        # Ensure a valid ETL module id is always present
        self.moduleid = (request.POST.get("module") if request else None) or details.get("etlmoduleid")
        self.loadid = loadid
        self.transactionid = transactionid
        self.params = params

    def record_load_event_outcome(self, complete, status, error_msg=None, load_details=None, user_id=None):
        """Record outcome of `load_event`.
        Prefer updating existing row; if none exists, insert with safe fallbacks.
        """
        # If no loadid has been established yet (e.g., during read/validation),
        # do not write to the database. Simply return so callers can surface the error.
        if not self.loadid:
            return

        # Ensure load_details is a dict before serializing
        if isinstance(load_details, str):
            try:
                load_details = json.loads(load_details)
            except Exception:
                load_details = {"raw": load_details}
        payload = json.dumps(load_details or {"error_message": error_msg})
        # Mirror core Arches behavior where successful is set at terminal states.
        successful = None
        if status in ["indexed", "unindexed", "unloaded", "cancelled"]:
            successful = True
        elif status == "failed":
            successful = False

        with connection.cursor() as cursor:
            # Try to update existing row first
            cursor.execute(
                """UPDATE load_event SET (complete, status, successful, error_message, load_details, load_end_time) = (%s, %s, %s, %s, %s, %s) WHERE loadid = (%s)""",
                (complete, status, successful, error_msg, payload, datetime.now(), self.loadid),
            )
            if cursor.rowcount == 0:
                # No existing row; insert a new one with required non-null fields
                cursor.execute(
                    """INSERT INTO load_event (loadid, complete, status, successful, error_message, load_details, etl_module_id, load_start_time, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        self.loadid,
                        complete,
                        status,
                        successful,
                        error_msg,
                        payload,
                        (self.moduleid or details.get("etlmoduleid")),
                        datetime.now(),
                        (user_id if user_id is not None else self.userid),
                    ),
                )

    def get_resourceid_values(self, request=None):
        """
        Reads CSV file and returns all values from the 'resourceinstanceid' or 'resourceid' column
        """
        content = request.FILES.get("file")
        if content.content_type == "text/csv":
            with NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in content.chunks():
                    tmp_file.write(chunk)
                tmp_file.flush()
                tmp_file.seek(0)

                with open(tmp_file.name, "r") as f:
                    reader = csv.DictReader(f)
                    resourceid_values = []

                    if reader.fieldnames:
                        reader.fieldnames = [
                            (fieldname.lstrip("\ufeff").strip() if isinstance(fieldname, str) else fieldname)
                            for fieldname in reader.fieldnames
                        ]

                    # Determine which resource id header to use: 'resourceinstanceid' or 'resourceid'
                    csv_fieldnames = (
                        {(fieldname.lower() if isinstance(fieldname, str) else fieldname): fieldname for fieldname in reader.fieldnames}
                        if reader.fieldnames
                        else {}
                    )

                    resource_id_key = None
                    if "resourceinstanceid" in csv_fieldnames:
                        resource_id_key = csv_fieldnames["resourceinstanceid"]
                    elif "resourceid" in csv_fieldnames:
                        resource_id_key = csv_fieldnames["resourceid"]
                    else:
                        error_msg = "Failed to read the values in your file due to incorrect headers.  Check you have a 'resourceinstanceid' or 'resourceid' column."
                        self.record_load_event_outcome(complete=False, status="failed", error_msg=error_msg)
                        return error_response(error_msg)

                    # Extract all values from the chosen resource id column
                    for row in reader:
                        value = row.get(resource_id_key)
                        if value:  # Skip empty values
                            # Normalize: trim whitespace and common stray characters
                            normalized_value = str(value).strip()
                            try:
                                # Validate UUID format on normalized value
                                uuid.UUID(normalized_value)
                                resourceid_values.append(normalized_value)
                            except Exception:
                                error_msg = (
                                    f"CSV Column {resource_id_key} contains invalid Resource ID values. '{value}' is not a valid UUID."
                                )
                                self.record_load_event_outcome(complete=False, status="failed", error_msg=error_msg)
                                return error_response(error_msg)
                    if len(resourceid_values) == 0:
                        error_msg = "No valid Resource ID values found in the CSV file."
                        self.record_load_event_outcome(complete=False, status="failed", error_msg=error_msg)
                        return error_response(error_msg)

                    return success_response(resourceid_values)
        else:
            return error_response("Invalid file type. Please upload a CSV file.")

    def read(self, request=None, source=None):

        # If CSV parsing returned an error dict, bubble it up

        resourceids = self.get_resourceid_values(request)

        if resourceids["success"]:
            # Shape `resourceids` as an object with nested `data` list to
            # match test expectations: result["data"]["resourceids"]["data"]
            resourceids["data"] = {
                "resourceids": {
                    "data": resourceids["data"],
                },
                "loadid": self.loadid,
                "transactionid": self.transactionid,
            }

        return resourceids

    def update_edit_log(self, resourceid, transactionid, user=None):
        """Keep edit_log entries up to date for edits performed in this bulk transaction."""

        try:
            models.EditLog.objects.filter(
                resourceid=resourceid,
                transactionid=transactionid,
                edittype="delete",
            ).update(
                userid=str(user.id) if user else None,
                user_email=user.email if user else "",
                user_firstname=user.first_name if user else "",
                user_lastname=user.last_name if user else "",
                user_username=user.username if user else "",
            )
            logging.info(
                f"Updated edit_log entries for resource {resourceid} and transaction {transactionid} with user ID {user.id if user else 'N/A'}."
            )
        except Exception as e:
            logging.warning(f"Unable to update edit_log entries for resource {resourceid} and transaction {transactionid}: {e}")

    def delete_resources(self, resourceids, userid, transactionid):
        """
        Deletes resources with the given resource instance IDs.
        """
        from arches.app.models.resource import Resource  # avoids circular import
        from django.contrib.auth.models import User  # Import User model

        user = User.objects.get(id=userid) if userid else {}

        resource_deleted_count = 0

        for resourceid in resourceids:
            try:
                resource_instance = Resource.objects.get(pk=resourceid)
                resource_instance.delete(user=user, transaction_id=transactionid)
                resource_deleted_count += 1
                self.update_edit_log(resourceid, transactionid, user)
            except Resource.DoesNotExist:
                logging.warning(f"Resource with ID {resourceid} does not exist and cannot be deleted.")
            except Exception as e:
                logging.error(f"Error deleting resource with ID {resourceid}: {str(e)}")

        # Keep editor metadata consistent in edit_log for async bulk deletions.
        # This is scoped to this transaction and delete edits only.

        if resource_deleted_count == len(resourceids):
            logging.info(f"Successfully deleted all {resource_deleted_count} resources.")
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE load_event SET (complete, status, successful, load_details, load_end_time) = (%s, %s, %s, %s, %s) WHERE loadid = (%s)""",
                    (
                        True,
                        "indexed",
                        True,
                        json.dumps({"deleted_resource_count": resource_deleted_count}),
                        datetime.now(),
                        self.loadid,
                    ),
                )

            return {"success": True, "data": "success"}
        else:
            error_msg = f"Deleted {resource_deleted_count} out of {len(resourceids)} resources. Check logs for details."
            logging.error(error_msg)
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE load_event SET (complete, status, successful, error_message, load_details, load_end_time) = (%s, %s, %s, %s, %s, %s) WHERE loadid = (%s)""",
                    (
                        True,
                        "failed",
                        False,
                        error_msg,
                        json.dumps({"deleted_count": resource_deleted_count, "total_count": len(resourceids)}),
                        datetime.now(),
                        self.loadid,
                    ),
                )
            return {"success": False, "data": error_msg}

    def run_bulk_deletion(self, request):
        self.loadid = request.POST.get("load_id")
        self.transactionid = request.POST.get("transaction_id")

        resourceids = self.read(request)

        if resourceids["success"] == False:
            error_msg = resourceids.get("data") or _(
                "Failed to read the values in your file. Check your file format and that you have a 'resourceinstanceid' or 'resourceid' column."
            )
            self.record_load_event_outcome(complete=True, status="failed", error_msg=error_msg)
            return error_response(error_msg)

        else:

            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO load_event (loadid, complete, status, load_details, etl_module_id, load_start_time, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        self.loadid,
                        False,
                        "validated",
                        json.dumps(
                            {
                                "transactionid": self.transactionid,
                                # Count of resource ids parsed from CSV
                                "resourceids_count": len(resourceids.get("data", {}).get("resourceids", {}).get("data", [])),
                            }
                        ),
                        # Guarantee NOT NULL value here
                        self.moduleid,
                        datetime.now(),
                        self.userid,
                    ),
                )

            response = self.run_bulk_task_async(request, self.loadid)

            return response

    @load_data_async
    def run_bulk_task_async(self, request):
        file_reader = self.read(request)
        if file_reader["success"] == True:
            # Extract the list of resource IDs from nested structure
            resourceids = file_reader["data"]["resourceids"]["data"]
            load_id = file_reader["data"]["loadid"]
            # Use the transaction id established from the incoming request/viewmodel.
            transaction_id = self.transactionid
            user_id = self.userid

            delete_task = proj_tasks.run_bulk_delete_resources.apply_async(
                (user_id, load_id, resourceids, transaction_id),
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE load_event SET taskid = %s WHERE loadid = %s""",
                    (delete_task.task_id, load_id),
                )

        else:
            # CSV parsing failed; record failure in load_event so summary can display it
            error_msg = file_reader.get("data") or _(
                "Failed to read the values in your file.  Check your file format and that you have a 'resourceinstanceid' or 'resourceid' column."
            )
            self.record_load_event_outcome(
                complete=False,
                status="failed",
                error_msg=error_msg,
                load_details={"error_message": error_msg},
            )
            return error_response(error_msg)

    def run_bulk_delete_task(self, userid, loadid, resourceids, transactionid):

        # In async execution, this instance is created without a request object.
        # Persist runtime context so delete audit entries can record the editor.
        self.userid = userid
        self.loadid = loadid
        self.transactionid = transactionid

        if resourceids:

            try:
                self.delete_resources(resourceids, userid, self.transactionid)
                self.record_load_event_outcome(
                    complete=True,
                    status="indexed",
                    error_msg=None,
                    load_details={"deleted_resource_count": len(resourceids), "transaction_id": self.transactionid},
                )

            except Exception as e:
                error_msg = f"An error occurred during resource deletion: {str(e)}"
                self.record_load_event_outcome(
                    complete=False,
                    status="failed",
                    error_msg=error_msg,
                )
