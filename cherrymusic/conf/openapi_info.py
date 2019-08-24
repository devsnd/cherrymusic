from drf_yasg import openapi

openapi_info = openapi.Info(
    title="CherryMusic API",
    default_version='v1',
    description="The internal CherryMusic API",
    license=openapi.License(name="GPL v3"),
)
