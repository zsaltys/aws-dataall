import logging
import os
import sys
import subprocess

# from .manager import stack
from ... import db
# from ...db import models
from ...db.api import Environment, Pipeline
# from ...utils.cdk_nag_utils import CDKNagUtil
# from ...utils.runtime_stacks_tagging import TagsUtil
from ...aws.handlers.sts import SessionHelper

logger = logging.getLogger(__name__)

# @stack(stack='cdkrepo')
class CDKPipelineStack:
    """
    Create a stack that contains CDK Continuous Integration and Delivery (CI/CD) pipeline.

    The pipeline is based on CodePipeline pipelines

    - Defaults for source/synth - CodeCommit & cdk synth
    - blueprint with DDK application code added in the CodeCommit repository <https://github.com/awslabs/aws-ddk>
    - ability to define development stages: dev, test, prod
    - ability to select gitflow or trunk-based as development strategy
    - Ability to connect to private artifactory to pull artifacts from at synth
    - Security best practices - ensures pipeline buckets block non-SSL, and are KMS-encrypted with rotated keys
    - data.all metadata as environment variables accesible at synth

    """
    def get_engine(self):
        envname = os.environ.get("envname", "local")
        engine = db.get_engine(envname=envname)
        return engine

    module_name = __file__

    def __init__(self, stack):
        engine = self.get_engine()
        with engine.scoped_session() as session:

            self.pipeline = Pipeline.get_pipeline_by_uri(session, stack.targetUri)
            self.pipeline_environment = Environment.get_environment_by_uri(session, self.pipeline.environmentUri)
            # Development environments
            self.development_environments = Pipeline.query_pipeline_environments(session, stack.targetUri)

        aws = SessionHelper.remote_session(self.pipeline_environment.AwsAccountId)
        env_creds = aws.get_credentials()

        python_path = '/:'.join(sys.path)[1:] + ':/code' + os.getenv('PATH')

        self.env = {
            'AWS_REGION': self.pipeline_environment.region,
            'AWS_DEFAULT_REGION': self.pipeline_environment.region,
            'CURRENT_AWS_ACCOUNT': self.pipeline_environment.AwsAccountId,
            'PYTHONPATH': python_path,
            'PATH': python_path,
            'envname': os.environ.get('envname', 'local'),
        }
        if env_creds:
            self.env.update(
                {
                    'AWS_ACCESS_KEY_ID': env_creds.access_key,
                    'AWS_SECRET_ACCESS_KEY': env_creds.secret_key,
                    'AWS_SESSION_TOKEN': env_creds.token
                }
            )

        self.code_dir_path = os.path.dirname(os.path.abspath(__file__))
        
        template = self.pipeline.template if (self.pipeline.template != self.pipeline.label) else ""

        self.initialize_repo(template)
        if not len(template):
            self.write_ddk_app_multienvironment(output_file="app.py")
            self.write_ddk_json_multienvironment(output_file="ddk.json")
        self.git_push_repo()

    def initialize_repo(self, template):

        template_cmds = [ 
            f"git clone {template} {self.pipeline.repo}",
            f"cd {self.pipeline.repo}",
            "rm -rf .git"
        ]
        no_template_cmds = [
            f"ddk init {self.pipeline.repo} --generate-only",
            f"cd {self.pipeline.repo}"
        ]
        repo_cmds = [
            "git init --initial-branch main",
            "virtualenv .venv && source .venv/bin/activate",
            "pip install -q -r requirements.txt",
            f"ddk create-repository {self.pipeline.repo} -t application dataall -t team {self.pipeline.SamlGroupName}"
        ]

        cmd_init = [ "pip install aws-ddk"] + (template_cmds if (self.pipeline.template != self.pipeline.label) else no_template_cmds ) + repo_cmds

        logger.info(f"Running Commands: {'; '.join(cmd_init)}")

        process = subprocess.run(
            '; '.join(cmd_init),
            text=True,
            shell=True,  # nosec
            encoding='utf-8',
            cwd=self.code_dir_path,
            env=self.env
        )
        if process.returncode == 0:
            logger.info("Successfully Initialized New CDK/DDK App")


    def write_ddk_json_multienvironment(self, output_file):
        json_envs = ""
        for env in self.development_environments:
            json_env = f""",
        "{env.stage}": {{
            "account": "{env.AwsAccountId}",
            "region": "{env.region}",
            "resources": {{
                "ddk-bucket": {{"versioned": false, "removal_policy": "destroy"}}
            }}
        }}"""
            json_envs = json_envs + json_env

        json = f"""{{
    "environments": {{
        "cicd": {{
            "account": "{self.pipeline_environment.AwsAccountId}",
            "region": "{self.pipeline_environment.region}"
        }}{json_envs}
    }}
}}"""

        with open(f'{self.code_dir_path}/{self.pipeline.repo}/{output_file}', 'w') as text_file:
            print(json, file=text_file)

    
    def write_ddk_app_multienvironment(self, output_file):
        header = f"""
# !/usr/bin/env python3

import aws_cdk as cdk
from aws_ddk_core.cicd import CICDPipelineStack
from ddk_app.ddk_app_stack import DdkApplicationStack
from aws_ddk_core.config import Config

app = cdk.App()

class ApplicationStage(cdk.Stage):
    def __init__(
            self,
            scope,
            environment_id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, f"dataall-{{environment_id.title()}}", **kwargs)
        DdkApplicationStack(self, "DataPipeline-{self.pipeline.label}-{self.pipeline.DataPipelineUri}", environment_id)

id = f"dataall-cdkpipeline-{self.pipeline.DataPipelineUri}"
config = Config()
(
    CICDPipelineStack(
        app,
        id=id,
        environment_id="cicd",
        pipeline_name="{self.pipeline.label}",
    )
        .add_source_action(repository_name="{self.pipeline.repo}")
        .add_synth_action()
        .build()"""

        stages = ""
        for env in sorted(self.development_environments, key=lambda env: env.order):
            stage = f""".add_stage("{env.stage}", ApplicationStage(app, "{env.stage}", env=config.get_env("{env.stage}")))"""
            stages = stages + stage
        footer = """
        .synth()
)

app.synth()
"""
        app = header + stages + footer
        with open(f'{self.code_dir_path}/{self.pipeline.repo}/{output_file}', 'w') as text_file:
            print(app, file=text_file)


    def git_push_repo(self):
        git_cmds = [
            'git config user.email "codebuild@example.com"',
            'git config user.name "CodeBuild"',
            'git config --local credential.helper "!aws codecommit credential-helper $@"',
            "git config --local credential.UseHttpPath true",
            "git add .",
            "git commit -a -m 'Initial Commit' ",
            "git push -u origin main"
        ]

        logger.info(f"Running Commands: {'; '.join(git_cmds)}")

        process = subprocess.run(
            '; '.join(git_cmds),
            text=True,
            shell=True,  # nosec
            encoding='utf-8',
            cwd=os.path.join(self.code_dir_path, self.pipeline.repo),
            env=self.env
        )
        if process.returncode == 0:
            logger.info("Successfully Pushed DDK App Code")

    @staticmethod
    def clean_up_repo(path):
        if path:
            precmd = [
                'rm',
                '-rf',
                f"{path}"
            ]

            cwd = os.path.dirname(os.path.abspath(__file__))
            logger.info(f"Running command : \n {' '.join(precmd)}")

            process = subprocess.run(
                ' '.join(precmd),
                text=True,
                shell=True,  # nosec
                encoding='utf-8',
                capture_output=True,
                cwd=cwd
            )

            if process.returncode == 0:
                print(f"Successfully cleaned cloned repo: {path}. {str(process.stdout)}")
            else:
                logger.error(
                    f'Failed clean cloned repo: {path} due to {str(process.stderr)}'
                )
        else:
            logger.info(f"Info:Path {path} not found")
        return