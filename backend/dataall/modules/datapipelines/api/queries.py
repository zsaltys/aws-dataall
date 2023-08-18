from dataall.base.api import gql
from dataall.modules.datapipelines.api.resolvers import list_pipelines, get_pipeline, ls, list_branches, cat, \
    get_creds, list_pipeline_environments, get_pipeline_environment

listDataPipelines = gql.QueryField(
    name='listDataPipelines',
    args=[gql.Argument(name='filter', type=gql.Ref('DataPipelineFilter'))],
    resolver=list_pipelines,
    type=gql.Ref('DataPipelineSearchResults'),
)

getDataPipeline = gql.QueryField(
    name='getDataPipeline',
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DataPipeline'),
    resolver=get_pipeline,
)


browseDataPipelineRepository = gql.QueryField(
    name='browseDataPipelineRepository',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('DataPipelineBrowseInput'))
        )
    ],
    resolver=ls,
    type=gql.String,
)

listDataPipelineBranches = gql.QueryField(
    name='listDataPipelineBranches',
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    resolver=list_branches,
    type=gql.ArrayType(gql.String),
)


getDataPipelineFileContent = gql.QueryField(
    name='getDataPipelineFileContent',
    args=[gql.Argument(name='input', type=gql.Ref('DataPipelineFileContentInput'))],
    resolver=cat,
    type=gql.String,
)

getDataPipelineCredsLinux = gql.QueryField(
    name='getDataPipelineCredsLinux',
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_creds,
)

listDataPipelineEnvironments = gql.QueryField(
    name='listDataPipelineEnvironments',
    args=[gql.Argument(name='filter', type=gql.Ref('DataPipelineEnvironmentFilter'))],
    resolver=list_pipeline_environments,
    type=gql.Ref('DataPipelineEnvironmentSearchResults'),
)

getDataPipelineEnvironment = gql.QueryField(
    name='getDataPipelineEnvironment',
    args=[gql.Argument(name='envPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DataPipelineEnvironment'),
    resolver=get_pipeline_environment,
)