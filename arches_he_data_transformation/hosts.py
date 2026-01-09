import re
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(
        re.sub(r"_", r"-", r"arches_he_data_transformation"),
        "arches_he_data_transformation.urls",
        name="arches_he_data_transformation",
    ),
)
