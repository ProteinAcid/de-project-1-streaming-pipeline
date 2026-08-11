from dagster import Definitions, define_asset_job, ScheduleDefinition
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


de_project_job = define_asset_job(
    name="de_project_job",
    selection=[de_project_dbt_assets]
)

de_project_schedule = ScheduleDefinition(
    job=de_project_job,
    cron_schedule="0 2 * * *"
)

defs = Definitions(
    assets=[de_project_dbt_assets],
    jobs=[de_project_job],
    schedules=[de_project_schedule],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project_path,
            profiles_dir="/home/vedantwork/.dbt"
        ),
    },
)