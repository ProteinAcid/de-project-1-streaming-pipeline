from dagster import Definitions
from dagster_dbt import DbtCliResource, dbt_assets, DbtProject
from pathlib import Path

dbt_project_path = Path(__file__).parent.parent / "de_project_transform"

dbt_project = DbtProject(
    project_dir=dbt_project_path,
    profiles_dir="/home/vedantwork/.dbt"
)
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def de_project_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


defs = Definitions(
    assets=[de_project_dbt_assets],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project_path,
            profiles_dir="/home/vedantwork/.dbt"
        ),
    },
)